from __future__ import annotations

import asyncio
import logging
import random
import re
import time
from os import path
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, Union
from urllib.parse import quote

import aiohttp
import orjson as json
from discord import Client
from discord.ext import commands
from discord.utils import MISSING
from websockets import client, exceptions
from websockets import typing as wstype

from . import __version__
from .enums import *
from .enums import LogLevel
from .events import NodeConnectedEvent, NodeDisconnectedEvent, NodeReconnectingEvent
from .exceptions import (
    LavalinkVersionIncompatible,
    NodeConnectionFailure,
    NodeCreationError,
    NodeNotAvailable,
    NodeRestException,
    NoNodesAvailable,
    TrackLoadError,
)
from .filters import Filter
from .objects import Playlist, Track
from .routeplanner import RoutePlanner
from .utils import (
    ExponentialBackoff,
    LavalinkVersion,
    NodeHealthMonitor,
    NodeStats,
    Ping,
)

if TYPE_CHECKING:
    from .player import Player

__all__ = (
    "Node",
    "NodePool",
)

VERSION_REGEX = re.compile(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[a-zA-Z0-9_-]+)?")


class Node:
    """The base class for a node.

    This node object represents a Lavalink v4 node.

    In Lavalink v4, all platform support (Spotify, Apple Music, Deezer, etc.)
    is handled by server-side plugins. You no longer need to provide API credentials
    to the client - configure them in your Lavalink server's application.yml instead.

    For lyrics support, ensure the LavaLyrics plugin is installed on your Lavalink server.
    """

    __slots__ = (
        "_bot",
        "_bot_user",
        "_host",
        "_port",
        "_pool",
        "_password",
        "_identifier",
        "_heartbeat",
        "_resume_key",
        "_resume_timeout",
        "_secure",
        "_fallback",
        "_log_level",
        "_websocket_uri",
        "_rest_uri",
        "_session",
        "_websocket",
        "_task",
        "_loop",
        "_session_id",
        "_available",
        "_version",
        "_headers",
        "_players",
        "_lyrics_enabled",
        "_route_planner",
        "_log",
        "_stats",
        "_backoff",
        "_health_monitor",
        "available",
    )

    def __init__(
        self,
        *,
        pool: Type[NodePool],
        bot: commands.Bot,
        host: str,
        port: int,
        password: str,
        identifier: str,
        secure: bool = False,
        heartbeat: int = 120,
        resume_key: Optional[str] = None,
        resume_timeout: int = 60,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        session: Optional[aiohttp.ClientSession] = None,
        lyrics: bool = False,
        fallback: bool = False,
        logger: Optional[logging.Logger] = None,
    ):
        if not isinstance(port, int):
            raise TypeError("Port must be an integer")

        self._bot: commands.Bot = bot
        self._host: str = host
        self._port: int = port
        self._pool: Type[NodePool] = pool
        self._password: str = password
        self._identifier: str = identifier
        self._heartbeat: int = heartbeat
        self._resume_key: Optional[str] = resume_key
        self._resume_timeout: int = resume_timeout
        self._secure: bool = secure
        self._fallback: bool = fallback

        self._websocket_uri: str = f"{'wss' if self._secure else 'ws'}://{self._host}:{self._port}"
        self._rest_uri: str = f"{'https' if self._secure else 'http'}://{self._host}:{self._port}"

        self._session: aiohttp.ClientSession = session  # type: ignore
        self._loop: asyncio.AbstractEventLoop = loop or asyncio.get_event_loop()
        self._websocket: client.WebSocketClientProtocol
        self._task: asyncio.Task = None  # type: ignore

        self._session_id: Optional[str] = None
        self._available: bool = False
        self._version: LavalinkVersion = LavalinkVersion(0, 0, 0)

        self._route_planner = RoutePlanner(self)
        self._log = logger
        self._lyrics_enabled: bool = lyrics
        self._backoff = ExponentialBackoff(base=7)
        self._health_monitor = NodeHealthMonitor(
            health_check_interval=30.0,
            circuit_breaker_threshold=5,
            circuit_timeout=60.0,
        )

        if not self._bot.user:
            raise NodeCreationError("Bot user is not ready yet.")

        self._bot_user = self._bot.user

        self._headers = {
            "Authorization": self._password,
            "User-Id": str(self._bot_user.id),
            "Client-Name": f"lava-lyra/{__version__}",
        }

        self._players: Dict[int, Player] = {}

        self._bot.add_listener(self._update_handler, "on_socket_response")

    def __repr__(self) -> str:
        return (
            f"<Lyra.node ws_uri={self._websocket_uri} rest_uri={self._rest_uri} "
            f"player_count={len(self._players)}>"
        )

    @property
    def is_connected(self) -> bool:
        """Property which returns whether this node is connected or not"""
        return self._websocket is not None and not self._websocket.closed

    @property
    def stats(self) -> NodeStats:
        """Property which returns the node stats."""
        return self._stats

    @property
    def players(self) -> Dict[int, Player]:
        """Property which returns a dict containing the guild ID and the player object."""
        return self._players

    @property
    def bot(self) -> Client:
        """Property which returns the discord.py client linked to this node"""
        return self._bot

    @property
    def player_count(self) -> int:
        """Property which returns how many players are connected to this node"""
        return len(self.players.values())

    @property
    def pool(self) -> Type[NodePool]:
        """Property which returns the pool this node is apart of"""
        return self._pool

    @property
    def latency(self) -> float:
        """Property which returns the latency of the node"""
        return Ping(self._host, port=self._port).get_ping()

    @property
    def ping(self) -> float:
        """Alias for `Node.latency`, returns the latency of the node"""
        return self.latency

    @property
    def lyrics_enabled(self) -> bool:
        """Property which returns whether lyrics support is enabled for this node"""
        return self._lyrics_enabled

    @property
    def health_monitor(self) -> NodeHealthMonitor:
        """Property which returns the node's health monitor"""
        return self._health_monitor

    @property
    def health_score(self) -> float:
        """Property which returns the current health score of the node"""
        current_latency = self.latency
        return self._health_monitor.get_health_score(current_latency, self.player_count)

    async def _handle_version_check(self, version: str) -> None:
        if version.endswith("-SNAPSHOT"):
            # we're just gonna assume all snapshot versions correlate with v4
            self._version = LavalinkVersion(major=4, minor=0, fix=0)
            return

        _version_rx = VERSION_REGEX.match(version)
        if not _version_rx:
            self._available = False
            raise LavalinkVersionIncompatible(
                "The Lavalink version you're using is incompatible. "
                "Lavalink version 3.7.0 or above is required to use this library.",
            )

        _version_groups = _version_rx.groups()
        major, minor, fix = (
            int(_version_groups[0] or 0),
            int(_version_groups[1] or 0),
            int(_version_groups[2] or 0),
        )

        if self._log:
            self._log.debug(f"Parsed Lavalink version: {major}.{minor}.{fix}")
        self._version = LavalinkVersion(major=major, minor=minor, fix=fix)
        if self._version < LavalinkVersion(3, 7, 0):
            self._available = False
            raise LavalinkVersionIncompatible(
                "The Lavalink version you're using is incompatible. "
                "Lavalink version 3.7.0 or above is required to use this library.",
            )

    # async def _set_ext_client_session(self, session: aiohttp.ClientSession) -> None:
    #     if self._spotify_client:
    #         await self._spotify_client._set_session(session=session)

    #     if self._apple_music_client:
    #         await self._apple_music_client._set_session(session=session)

    async def _update_handler(self, data: dict) -> None:
        await self._bot.wait_until_ready()

        if not data:
            return

        if data["t"] == "VOICE_SERVER_UPDATE":
            guild_id = int(data["d"]["guild_id"])
            try:
                player = self._players[guild_id]
                await player.on_voice_server_update(data["d"])
            except KeyError:
                return

        elif data["t"] == "VOICE_STATE_UPDATE":
            if int(data["d"]["user_id"]) != self._bot_user.id:
                return

            guild_id = int(data["d"]["guild_id"])
            try:
                player = self._players[guild_id]
                await player.on_voice_state_update(data["d"])
            except KeyError:
                return

    async def _handle_node_switch(self) -> None:
        nodes = [
            node
            for node in self.pool._nodes.copy().values()
            if node._available and node != self and node._session_id
        ]

        if not nodes:
            if self._log:
                self._log.warning(f"No available backup nodes for {self._identifier}")
            return

        # Select best node based on health score instead of random selection
        # This ensures players migrate to the healthiest available node
        node_scores = {node: node.health_score for node in nodes}
        new_node = max(node_scores, key=node_scores.get)  # type: ignore

        if self._log:
            self._log.info(
                f"Selected node {new_node._identifier} for failover "
                f"(health score: {new_node.health_score:.1f})"
            )

        for player in self.players.copy().values():
            try:
                await player._swap_node(new_node=new_node)
            except Exception as e:
                if self._log:
                    self._log.error(f"Failed to switch player {player._guild.id}: {e}")

        if self._log:
            self._log.info(
                f"All players switched from {self._identifier} to {new_node._identifier}, "
                f"node will attempt reconnection"
            )

    async def _configure_resuming(self) -> None:
        if not self._resume_key:
            return

        data: Dict[str, Union[int, str, bool]] = {"timeout": self._resume_timeout}

        if self._version.major == 3:
            data["resumingKey"] = self._resume_key
        elif self._version.major == 4:
            if self._log:
                self._log.warning("Using a resume key with Lavalink v4 is deprecated.")
            data["resuming"] = True

        try:
            await self.send(
                method="PATCH",
                path=f"sessions/{self._session_id}",
                include_version=True,
                data=data,
            )
            if self._log:
                self._log.debug("Resume configuration applied successfully")
        except Exception as e:
            if self._log:
                self._log.warning(f"Failed to configure resuming: {e}")

    async def _listen(self) -> None:
        while True:
            try:
                msg = await self._websocket.recv()
                data = json.loads(msg)
                if self._log:
                    self._log.debug(f"Recieved raw websocket message {msg}")
                self._loop.create_task(self._handle_ws_msg(data=data))
            except exceptions.ConnectionClosed:
                if self._log:
                    self._log.warning(f"WebSocket connection to node {self._identifier} closed")

                self._session_id = None
                self._available = False

                # Record connection failure in health monitor
                self._health_monitor.record_failure()

                # Dispatch node disconnected event
                player_count = self.player_count
                event = NodeDisconnectedEvent(self._identifier, player_count)
                event.dispatch(self._bot)

                # If fallback is enabled, switch players to another node
                # Otherwise, destroy them
                if self._fallback and self.player_count > 0:
                    await self._handle_node_switch()
                elif self.player_count > 0:
                    for _player in self.players.copy().values():
                        self._loop.create_task(_player.destroy())

                # Close the websocket if it's not already closed
                if self._websocket and not self._websocket.closed:
                    self._loop.create_task(self._websocket.close())

                retry = self._backoff.delay()
                if self._log:
                    self._log.warning(
                        f"Retrying connection to Node {self._identifier} in {retry:.1f} secs",
                    )

                # Dispatch node reconnecting event
                event = NodeReconnectingEvent(self._identifier, retry)
                event.dispatch(self._bot)

                await asyncio.sleep(retry)

                if not self.is_connected:
                    try:
                        await self.connect(reconnect=True)

                        # Record successful reconnection in health monitor
                        self._health_monitor.record_reconnection()
                        self._health_monitor.record_success()

                        if self._log:
                            self._log.warning(
                                f"Successfully reconnected to node {self._identifier}"
                            )
                        # Continue the loop to start listening for messages
                        continue
                    except Exception as e:
                        if self._log:
                            self._log.error(f"Failed to reconnect to node {self._identifier}: {e}")
                        # Record failure in health monitor
                        self._health_monitor.record_failure()
                        # Continue the loop to retry again
                        continue

    async def _handle_ws_msg(self, data: dict) -> None:
        if self._log:
            self._log.debug(f"Recieved raw payload from Node {self._identifier} with data {data}")
        op = data.get("op", None)

        if op == "stats":
            self._stats = NodeStats(data)
            return

        if op == "ready":
            old_session_id = self._session_id
            self._session_id = data["sessionId"]

            if self._log:
                self._log.info(f"Node {self._identifier} ready with session {self._session_id}")

            if old_session_id and old_session_id != self._session_id:
                if self._log:
                    self._log.info(
                        f"Session ID changed from {old_session_id} to {self._session_id}, updating players"
                    )
                for player in self._players.values():
                    await player._refresh_endpoint_uri(self._session_id)

            await self._configure_resuming()
            self._available = True

        if not "guildId" in data:
            return

        player: Optional[Player] = self._players.get(int(data["guildId"]))
        if not player:
            return

        if op == "event":
            return await player._dispatch_event(data)

        if op == "playerUpdate":
            return await player._update_state(data)

    async def send(
        self,
        method: str,
        path: str,
        include_version: bool = True,
        guild_id: Optional[Union[int, str]] = None,
        query: Optional[str] = None,
        data: Optional[Union[Dict, str]] = None,
        ignore_if_available: bool = False,
    ) -> Any:
        if not ignore_if_available and not self._available:
            raise NodeNotAvailable(
                f"The node '{self._identifier}' is unavailable.",
            )

        if not ignore_if_available and not self._session_id and "sessions/" in path:
            if self._log:
                self._log.warning(
                    f"No session ID available for node {self._identifier}, waiting for reconnection"
                )
            raise NodeNotAvailable(
                f"The node '{self._identifier}' has no active session.",
            )

        uri: str = (
            f"{self._rest_uri}/"
            f'{f"v{self._version.major}/" if include_version else ""}'
            f"{path}"
            f'{f"/{guild_id}" if guild_id else ""}'
            f'{f"?{query}" if query else ""}'
        )

        try:
            resp = await self._session.request(
                method=method,
                url=uri,
                headers=self._headers,
                json=data or {},
            )

            if self._log:
                self._log.debug(
                    f"Making REST request to Node {self._identifier} with method {method} to {uri}",
                )

            if resp.status >= 300:
                resp_data: dict = await resp.json()

                if resp.status == 404 and "session" in resp_data.get("message", "").lower():
                    if self._log:
                        self._log.warning(
                            f"Session not found error from {self._identifier}, marking as unavailable"
                        )
                    self._available = False
                    self._session_id = None

                raise NodeRestException(
                    f'Error from Node {self._identifier} fetching from Lavalink REST api: {resp.status} {resp.reason}: {resp_data["message"]}',
                )

            if method == "DELETE" or resp.status == 204:
                if self._log:
                    self._log.debug(
                        f"REST request to Node {self._identifier} with method {method} to {uri} completed sucessfully and returned no data.",
                    )
                return await resp.json(content_type=None)

            if resp.content_type == "text/plain":
                if self._log:
                    self._log.debug(
                        f"REST request to Node {self._identifier} with method {method} to {uri} completed sucessfully and returned text with body {await resp.text()}",
                    )
                return await resp.text()

            if self._log:
                self._log.debug(
                    f"REST request to Node {self._identifier} with method {method} to {uri} completed sucessfully and returned JSON with body {await resp.json()}",
                )
            return await resp.json()

        except aiohttp.ClientError as e:
            if self._log:
                self._log.error(f"HTTP client error when connecting to {self._identifier}: {e}")
            self._available = False
            raise NodeNotAvailable(f"HTTP error connecting to node {self._identifier}: {e}")

    def get_player(self, guild_id: int) -> Optional[Player]:
        """Takes a guild ID as a parameter. Returns a lyra Player object or None."""
        return self._players.get(guild_id, None)

    async def connect(self, *, reconnect: bool = False) -> Node:
        """Initiates a connection with a Lavalink node and adds it to the node pool."""
        await self._bot.wait_until_ready()

        start = time.perf_counter()

        if not self._session:
            # Configure connection pooling for optimal concurrent request performance
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connection limit
                limit_per_host=30,  # Per-host connection limit
                ttl_dns_cache=300,  # DNS cache TTL in seconds
            )
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
            )

        try:
            if not reconnect:
                version: str = await self.send(
                    method="GET",
                    path="version",
                    ignore_if_available=True,
                    include_version=False,
                )

                await self._handle_version_check(version=version)
                # await self._set_ext_client_session(session=self._session)

                if self._log:
                    self._log.debug(
                        f"Version check from Node {self._identifier} successful. Returned version {version}",
                    )

            if reconnect:
                self._session_id = None
                self._available = False

            self._websocket = await client.connect(
                f"{self._websocket_uri}/v{self._version.major}/websocket",
                extra_headers=self._headers,
                ping_interval=self._heartbeat,
            )

            if reconnect:
                if self._log:
                    self._log.info(f"Successfully reconnected to Node {self._identifier}")

            if self._log:
                self._log.debug(
                    f"Node {self._identifier} successfully connected to websocket using {self._websocket_uri}/v{self._version.major}/websocket",
                )

            if not self._task or self._task.done():
                self._task = self._loop.create_task(self._listen())

            end = time.perf_counter()

            # Dispatch node connected event
            event = NodeConnectedEvent(self._identifier, reconnect)
            event.dispatch(self._bot)

            # Record successful connection in health monitor
            if not reconnect:
                self._health_monitor.record_success()

            if self._log:
                self._log.info(f"Connected to node {self._identifier}. Took {end - start:.3f}s")
            return self

        except (aiohttp.ClientConnectorError, OSError, ConnectionRefusedError) as e:
            self._health_monitor.record_failure()
            raise NodeConnectionFailure(
                f"The connection to node '{self._identifier}' failed: {e}",
            ) from None
        except exceptions.InvalidHandshake:
            self._health_monitor.record_failure()
            raise NodeConnectionFailure(
                f"The password for node '{self._identifier}' is invalid: {e}",
            ) from None
        except exceptions.InvalidURI:
            self._health_monitor.record_failure()
            raise NodeConnectionFailure(
                f"The URI for node '{self._identifier}' is invalid: {e}",
            ) from None

    async def disconnect(self) -> None:
        """Disconnects a connected Lavalink node and removes it from the node pool.
        This also destroys any players connected to the node.
        """

        start = time.perf_counter()

        for player in self.players.copy().values():
            await player.destroy()
            if self._log:
                self._log.debug("All players disconnected from node.")

        await self._websocket.close()
        await self._session.close()
        if self._log:
            self._log.debug("Websocket and http session closed.")

        del self._pool._nodes[self._identifier]
        self.available = False
        self._task.cancel()

        end = time.perf_counter()
        if self._log:
            self._log.info(
                f"Successfully disconnected from node {self._identifier} and closed all sessions. Took {end - start:.3f}s",
            )

    async def build_track(self, identifier: str, ctx: Optional[commands.Context] = None) -> Track:
        """
        Builds a track using a valid track identifier

        You can also pass in a discord.py Context object to get a
        Context object on the track it builds.
        """

        data: dict = await self.send(
            method="GET",
            path="decodetrack",
            query=f"encodedTrack={quote(identifier)}",
        )

        track_info = data["info"] if self._version.major >= 4 else data

        return Track(
            track_id=identifier,
            ctx=ctx,
            info=track_info,
            track_type=TrackType(track_info["sourceName"]),
        )

    async def get_tracks(
        self,
        query: str,
        *,
        ctx: Optional[commands.Context] = None,
        search_type: Optional[SearchType] = SearchType.ytsearch,
        filters: Optional[List[Filter]] = None,
    ) -> Optional[Union[Playlist, List[Track]]]:
        """Fetches tracks from the node's REST api to parse into Lavalink.

        In Lavalink v4, all platform support is handled by server-side plugins.
        Spotify, Apple Music, Deezer, etc. URLs are passed directly to Lavalink
        which uses plugins like LavaSrc to handle them.

        Args:
            query: Search query or URL
            ctx: Discord context for the track
            search_type: Search type to use if query is not a URL
            filters: Filters to apply to tracks when they play
        """

        timestamp = None

        if filters:
            for filter in filters:
                filter.set_preload()

        # In Lavalink v4, we simply pass URLs directly to Lavalink
        # The server-side plugins (LavaSrc, etc.) handle the parsing

        # Check if this is a platform URL that should be passed directly

        is_platform_url = (
            URLRegex.SPOTIFY_URL.match(query)
            or URLRegex.AM_URL.match(query)
            or URLRegex.SOUNDCLOUD_URL.match(query)
            or URLRegex.YOUTUBE_URL.match(query)
            or URLRegex.BILIBILI_URL.match(query)
        )

        if not is_platform_url:
            # Apply search prefix for non-URL queries
            if (
                search_type
                and not URLRegex.BASE_URL.match(query)
                and not re.match(r"(?:[a-z]+?)search:.", query)
                and not URLRegex.DISCORD_MP3_URL.match(query)
                and not path.exists(path.dirname(query))
            ):
                query = f"{search_type}:{query}"

        # Capture YouTube timestamp if present
        if match := URLRegex.YOUTUBE_TIMESTAMP.match(query):
            timestamp = float(match.group("time"))

        # Make request to Lavalink
        data = await self.send(
            method="GET",
            path="loadtracks",
            query=f"identifier={quote(query)}",
        )

        load_type = data.get("loadType")
        data_type = "data" if self._version.major >= 4 else "tracks"

        if not load_type:
            raise TrackLoadError(
                "There was an error while trying to load this track.",
            )

        elif load_type in ("LOAD_FAILED", "error"):
            exception = data["data"] if self._version.major >= 4 else data["exception"]
            raise TrackLoadError(
                f"{exception['message']} [{exception['severity']}]",
            )

        elif load_type in ("NO_MATCHES", "empty"):
            return None

        elif load_type in ("PLAYLIST_LOADED", "playlist"):
            if self._version.major >= 4:
                track_list = data[data_type]["tracks"]
                playlist_info = data[data_type]["info"]
            else:
                track_list = data[data_type]
                playlist_info = data["playlistInfo"]

            tracks = [
                Track(
                    track_id=track["encoded"],
                    info=track["info"],
                    ctx=ctx,
                    track_type=TrackType(track["info"]["sourceName"]),
                )
                for track in track_list
            ]

            return Playlist(
                playlist_info=playlist_info,
                tracks=tracks,
                playlist_type=PlaylistType(tracks[0].track_type.value),
                thumbnail=tracks[0].thumbnail,
                uri=query,
            )

        elif load_type in ("SEARCH_RESULT", "TRACK_LOADED", "track", "search"):
            if self._version.major >= 4 and isinstance(data[data_type], dict):
                data[data_type] = [data[data_type]]

            # Handle local files
            if path.exists(path.dirname(query)):
                local_file = Path(query)
                return [
                    Track(
                        track_id=track["encoded"],
                        info={
                            "title": local_file.name,
                            "author": "Unknown",
                            "length": track["info"]["length"],
                            "uri": quote(local_file.as_uri()),
                            "position": track["info"]["position"],
                            "identifier": track["info"]["identifier"],
                        },
                        ctx=ctx,
                        track_type=TrackType.LOCAL,
                        filters=filters,
                    )
                    for track in data[data_type]
                ]

            # Handle Discord attachments
            elif discord_url := URLRegex.DISCORD_MP3_URL.match(query):
                return [
                    Track(
                        track_id=track["encoded"],
                        info={
                            "title": discord_url.group("file"),
                            "author": "Unknown",
                            "length": track["info"]["length"],
                            "uri": track["info"]["uri"],
                            "position": track["info"]["position"],
                            "identifier": track["info"]["identifier"],
                        },
                        ctx=ctx,
                        track_type=TrackType.HTTP,
                        filters=filters,
                    )
                    for track in data[data_type]
                ]

            # Handle normal tracks
            return [
                Track(
                    track_id=track["encoded"],
                    info=track["info"],
                    ctx=ctx,
                    track_type=TrackType(track["info"]["sourceName"]),
                    filters=filters,
                    timestamp=timestamp,
                )
                for track in data[data_type]
            ]

        else:
            raise TrackLoadError(
                "There was an error while trying to load this track.",
            )

    async def get_recommendations(
        self,
        *,
        track: Track,
        ctx: Optional[commands.Context] = None,
    ) -> Optional[Union[List[Track], Playlist]]:
        """
        Gets recommendations for a track.

        In Lavalink v4, recommendations are handled by plugins.
        For Spotify tracks, use the 'sprec:' search prefix.
        For YouTube tracks, use the autoplay/radio playlist.

        Args:
            track: The track to get recommendations for
            ctx: Discord context for recommended tracks

        Returns:
            List of recommended tracks or None if not supported
        """
        if track.track_type == TrackType.SPOTIFY:
            # Use Spotify recommendations via LavaSrc plugin
            return await self.get_tracks(
                query=track.identifier,
                search_type=SearchType.sprec,
                ctx=ctx,
            )

        elif track.track_type == TrackType.YOUTUBE:
            # Use YouTube autoplay/radio playlist
            return await self.get_tracks(
                query=f"https://www.youtube.com/watch?v={track.identifier}&list=RD{track.identifier}",
                search_type=SearchType.ytsearch,
                ctx=ctx,
            )

        else:
            raise TrackLoadError(
                "Recommendations are only supported for Spotify and YouTube tracks. "
                "Make sure the appropriate plugins are installed on your Lavalink server.",
            )


class NodePool:
    """The base class for the node pool.
    This holds all the nodes that are to be used by the bot.
    """

    __slots__ = ()
    _nodes: Dict[str, Node] = {}

    def __repr__(self) -> str:
        return f"<Lyra.NodePool node_count={self.node_count}>"

    @property
    def nodes(self) -> Dict[str, Node]:
        """Property which returns a dict with the node identifier and the Node object."""
        return self._nodes

    @property
    def node_count(self) -> int:
        return len(self._nodes.values())

    @classmethod
    def get_best_node(cls, *, algorithm: NodeAlgorithm) -> Node:
        """Fetches the best node based on an NodeAlgorithm.
        This option is preferred if you want to choose the best node
        from a multi-node setup using either the node's latency,
        player count, or overall health score.

        Use NodeAlgorithm.by_ping if you want to get the best node
        based on the node's latency.

        Use NodeAlgorithm.by_players if you want to get the best node
        based on how many players it has. This method will return a node with
        the least amount of players.

        Use NodeAlgorithm.by_health if you want to get the best node
        based on overall health score (latency, uptime, load, stability).
        This is recommended for production multi-node setups.
        """
        available_nodes: List[Node] = [node for node in cls._nodes.values() if node._available]

        if not available_nodes:
            raise NoNodesAvailable("There are no nodes available.")

        # Filter out nodes with open circuit breaker
        healthy_nodes = [
            node for node in available_nodes if not node._health_monitor.is_circuit_open
        ]

        # If all nodes have open circuit breakers, use all available nodes
        # (emergency fallback)
        nodes_to_consider = healthy_nodes if healthy_nodes else available_nodes

        if algorithm == NodeAlgorithm.by_ping:
            tested_nodes = {node: node.latency for node in nodes_to_consider}
            return min(tested_nodes, key=tested_nodes.get)  # type: ignore

        elif algorithm == NodeAlgorithm.by_players:
            tested_nodes = {node: len(node.players.keys()) for node in nodes_to_consider}
            return min(tested_nodes, key=tested_nodes.get)  # type: ignore

        elif algorithm == NodeAlgorithm.by_health:
            # Higher health score is better
            tested_nodes = {node: node.health_score for node in nodes_to_consider}
            return max(tested_nodes, key=tested_nodes.get)  # type: ignore

        else:
            raise ValueError(
                "The algorithm provided is not a valid NodeAlgorithm.",
            )

    @classmethod
    def get_node(cls, *, identifier: Optional[str] = None) -> Node:
        """Fetches a node from the node pool using it's identifier.
        If no identifier is provided, it will choose a node at random.
        """
        available_nodes = {
            identifier: node for identifier, node in cls._nodes.items() if node._available
        }

        if not available_nodes:
            raise NoNodesAvailable("There are no nodes available.")

        if identifier is None:
            return random.choice(list(available_nodes.values()))

        return available_nodes[identifier]

    @classmethod
    async def create_node(
        cls,
        *,
        bot: commands.Bot,
        host: str,
        port: int,
        password: str,
        identifier: str,
        secure: bool = False,
        heartbeat: int = 120,
        resume_key: Optional[str] = None,
        resume_timeout: int = 60,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        session: Optional[aiohttp.ClientSession] = None,
        lyrics: bool = False,
        fallback: bool = False,
        logger: Optional[logging.Logger] = None,
    ) -> Node:
        """Creates a Node object to be then added into the node pool.

        In Lavalink v4, platform support (Spotify, Apple Music, etc.) is handled
        by server-side plugins. Configure these in your Lavalink server's
        application.yml file instead of passing credentials to the client.
        """
        if identifier in cls._nodes.keys():
            raise NodeCreationError(
                f"A node with identifier '{identifier}' already exists.",
            )

        node = Node(
            pool=cls,
            bot=bot,
            host=host,
            port=port,
            password=password,
            identifier=identifier,
            secure=secure,
            heartbeat=heartbeat,
            resume_key=resume_key,
            resume_timeout=resume_timeout,
            loop=loop,
            session=session,
            lyrics=lyrics,
            fallback=fallback,
            logger=logger,
        )

        await node.connect()
        cls._nodes[node._identifier] = node
        return node

    @classmethod
    async def disconnect(cls) -> None:
        """Disconnects all available nodes from the node pool."""

        available_nodes: List[Node] = [node for node in cls._nodes.values() if node._available]

        for node in available_nodes:
            await node.disconnect()
