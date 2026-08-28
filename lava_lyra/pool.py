from __future__ import annotations

import asyncio
import logging
import random
import re
import time
from os import path
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, cast
from urllib.parse import quote

import aiohttp
import orjson as json
from websockets import State, exceptions
from websockets.asyncio.client import ClientConnection
from websockets.asyncio.client import connect as ws_connect

from . import __version__
from .compat import BotType, ContextType
from .enums import *
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
from .search import SearchManager, SearchResult
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

_VERSION_REGEX = re.compile(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[a-zA-Z0-9_-]+)?")


class Node:
    """The base class for a node.

    This node object represents a Lavalink v4 node.

    In Lavalink v4, all platform support (Spotify, Apple Music, Deezer, etc.)
    is handled by server-side plugins. You no longer need to provide API credentials
    to the client - configure them in your Lavalink server's application.yml instead.

    For lyrics support, ensure the LavaLyrics plugin is installed on your Lavalink or NodeLink server.
    """

    __slots__ = (
        "_available",
        "_backoff",
        "_bot",
        "_bot_user",
        "_connect_timeout",
        "_dispatched_disconnect",
        "_enabled",
        "_fallback",
        "_headers",
        "_health_monitor",
        "_heartbeat",
        "_host",
        "_identifier",
        "_is_nodelink",
        "_last_session_id",
        "_latency_cache",
        "_latency_task",
        "_log",
        "_loop",
        "_lyrics_enabled",
        "_password",
        "_players",
        "_pool",
        "_port",
        "_rest_uri",
        "_resume_key",
        "_resume_timeout",
        "_route_planner",
        "_search_enabled",
        "_search_manager",
        "_secure",
        "_session",
        "_session_id",
        "_stats",
        "_task",
        "_total_timeout",
        "_version",
        "_websocket",
        "_websocket_uri",
    )

    _LATENCY_CACHE_TTL: ClassVar[float] = 5.0

    _RECOMMENDATION_SEARCH_TYPES: ClassVar[dict[TrackType, SearchType]] = {
        TrackType.SPOTIFY: SearchType.sprec,
        TrackType.DEEZER: SearchType.dzrec,
        TrackType.TIDAL: SearchType.tdrec,
        TrackType.JIOSAAVN: SearchType.jsrec,
    }

    def __init__(
        self,
        *,
        pool: type[NodePool],
        bot: BotType,
        host: str,
        port: int,
        password: str,
        identifier: str,
        enabled: bool = True,
        secure: bool = False,
        heartbeat: int = 120,
        resume_key: str | None = None,
        resume_timeout: int = 60,
        loop: asyncio.AbstractEventLoop | None = None,
        session: aiohttp.ClientSession | None = None,
        lyrics: bool = False,
        search: bool = False,
        fallback: bool = False,
        logger: logging.Logger | None = None,
        circuit_breaker_threshold: int = 5,
        circuit_timeout: float = 60.0,
        connect_timeout: float = 10.0,
        total_timeout: float = 30.0,
    ):
        if not isinstance(port, int):
            raise TypeError("Port must be an integer")

        self._bot: BotType = bot
        self._host: str = host
        self._port: int = port
        self._pool: type[NodePool] = pool
        self._password: str = password
        self._identifier: str = identifier
        self._heartbeat: int = heartbeat
        self._resume_key: str | None = resume_key
        self._resume_timeout: int = resume_timeout
        self._secure: bool = secure
        self._fallback: bool = fallback
        self._enabled: bool = enabled
        self._connect_timeout: float = connect_timeout
        self._total_timeout: float = total_timeout

        self._websocket_uri: str = f"{'wss' if self._secure else 'ws'}://{self._host}:{self._port}"
        self._rest_uri: str = f"{'https' if self._secure else 'http'}://{self._host}:{self._port}"

        self._session: aiohttp.ClientSession | None = session
        self._loop: asyncio.AbstractEventLoop = loop or asyncio.get_event_loop()
        self._websocket: ClientConnection | None = None
        self._task: asyncio.Task[Any] | None = None

        self._session_id: str | None = None
        self._last_session_id: str | None = None
        self._available: bool = False
        self._dispatched_disconnect: bool = False
        self._is_nodelink: bool = False
        self._version: LavalinkVersion = LavalinkVersion(0, 0, 0)

        self._latency_cache: float | None = None
        self._latency_task: asyncio.Task[Any] | None = None

        self._stats: NodeStats = NodeStats(
            {
                "memory": {"used": 0, "free": 0, "reservable": 0, "allocated": 0},
                "cpu": {"cores": 0, "systemLoad": 0.0, "lavalinkLoad": 0.0},
                "playingPlayers": 0,
                "players": 0,
                "uptime": 0,
            }
        )

        self._route_planner: RoutePlanner = RoutePlanner(self)
        self._search_manager: SearchManager = SearchManager(self)
        self._log: logging.Logger | None = logger
        self._lyrics_enabled: bool = lyrics
        self._search_enabled: bool = search
        self._backoff: ExponentialBackoff = ExponentialBackoff(base=7)
        self._health_monitor: NodeHealthMonitor = NodeHealthMonitor(
            circuit_breaker_threshold=circuit_breaker_threshold,
            circuit_timeout=circuit_timeout,
        )

        if not self._bot.user:
            raise NodeCreationError("Bot user is not ready yet.")

        self._bot_user = self._bot.user

        self._headers = {
            "Authorization": self._password,
            "User-Id": str(self._bot_user.id),
            "Client-Name": f"lava-lyra/{__version__}",
        }

        self._players: dict[int, Player] = {}

    def __repr__(self) -> str:
        return (
            f"<Lyra.node ws_uri={self._websocket_uri} rest_uri={self._rest_uri} "
            f"player_count={len(self._players)}>"
        )

    @property
    def identifier(self) -> str:
        """Property which returns this node's identifier"""
        return self._identifier

    @property
    def enabled(self) -> bool:
        """Whether this node is enabled and allowed to connect."""
        return self._enabled

    @property
    def is_connected(self) -> bool:
        """Property which returns whether this node is connected or not"""
        return self._websocket is not None and self._websocket.state is not State.CLOSED

    @property
    def stats(self) -> NodeStats:
        """Property which returns the node stats."""
        return self._stats

    @property
    def players(self) -> dict[int, Player]:
        """Property which returns a dict containing the guild ID and the player object."""
        return self._players

    @property
    def bot(self) -> BotType:
        """Property which returns the Discord.py or Py-cord client linked to this node"""
        return self._bot

    @property
    def player_count(self) -> int:
        """Property which returns how many players are connected to this node"""
        return len(self.players.values())

    @property
    def pool(self) -> type[NodePool]:
        """Property which returns the pool this node is apart of"""
        return self._pool

    @property
    def route_planner(self) -> RoutePlanner:
        """Property which returns this node's route planner"""
        return self._route_planner

    @property
    def latency(self) -> float:
        if self._latency_cache is None:
            if not self._latency_task or self._latency_task.done():
                self._latency_task = self._loop.create_task(self._latency_probe_loop())
            return -1.0

        return self._latency_cache

    async def _latency_probe_loop(self) -> None:
        while True:
            try:
                value = await self._loop.run_in_executor(
                    None,
                    Ping(self._host, port=self._port).get_ping,
                )
                self._latency_cache = value
                self._health_monitor.quality_tracker.record_latency(value)
            except asyncio.CancelledError:
                raise
            except Exception:
                if self._log:
                    self._log.debug(
                        f"Latency probe failed for node {self._identifier}",
                        exc_info=True,
                    )
            await asyncio.sleep(self._LATENCY_CACHE_TTL)

    @property
    def ping(self) -> float:
        """Alias for `Node.latency`, returns the latency of the node"""
        return self.latency

    @property
    def lyrics_enabled(self) -> bool:
        """Property which returns whether lyrics support is enabled for this node"""
        return self._lyrics_enabled

    @property
    def search_enabled(self) -> bool:
        """Property which returns whether LavaSearch plugin support is enabled for this node"""
        return self._search_enabled

    @property
    def health_monitor(self) -> NodeHealthMonitor:
        """Property which returns the node's health monitor"""
        return self._health_monitor

    @property
    def health_score(self) -> float:
        """Property which returns the current health score of the node"""
        current_latency = self.latency
        return self._health_monitor.get_health_score(current_latency, self.player_count)

    async def enable(self) -> None:
        """Enable this node and attempt to connect if not already connected."""
        self._enabled = True
        if not self.is_connected:
            await self.connect()

    async def disable(self) -> None:
        """Disable this node and disconnect if connected."""
        self._enabled = False
        self._available = False
        self._latency_cache = None
        if self._latency_task:
            self._latency_task.cancel()
        if self.is_connected and self._websocket:
            await self._websocket.close()

    async def _handle_version_check(self, version: str) -> None:
        if version.endswith("-SNAPSHOT"):
            self._version = LavalinkVersion(major=4, minor=2, fix=0)
            return

        _version_rx = _VERSION_REGEX.match(version)
        if not _version_rx:
            self._available = False
            raise LavalinkVersionIncompatible(
                "The Lavalink version you're using is incompatible. "
                "Lavalink version 4.2.0 or above is required to use this library.",
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

        if not self._is_nodelink and self._version < LavalinkVersion(4, 2, 0):
            self._available = False
            raise LavalinkVersionIncompatible(
                "The Lavalink version you're using is incompatible. "
                "Lavalink version 4.2.0 or above is required to use this library.",
            )

        if self._is_nodelink and self._version < LavalinkVersion(3, 2, 0):
            self._available = False
            raise LavalinkVersionIncompatible(
                "The NodeLink version you're using is incompatible. "
                "NodeLink version 3.2.0 or above is required to use this library.",
            )

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
        node_scores: dict[Node, float] = {node: node.health_score for node in nodes}
        new_node = max(node_scores, key=node_scores.__getitem__)

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

        data: dict[str, int | str | bool] = {"timeout": self._resume_timeout}

        if self._is_nodelink:
            data["resuming"] = True
        elif self._version.major == 3:
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

    def _log_task_exception(self, task: asyncio.Task[Any]) -> None:
        if task.cancelled():
            return
        exc = task.exception()
        if exc and self._log:
            self._log.error(f"Unhandled exception in websocket message task: {exc!r}", exc_info=exc)

    async def _listen(self) -> None:
        while True:
            try:
                if not self._websocket:
                    break
                msg = await self._websocket.recv()
                try:
                    data = json.loads(msg)
                except json.JSONDecodeError as e:
                    if self._log:
                        self._log.warning(
                            f"Node {self._identifier} sent a malformed (non-JSON) websocket message, ignoring: {e}",
                        )
                    continue
                if self._log:
                    self._log.debug(f"Recieved raw websocket message {msg!r}")
                task = self._loop.create_task(self._handle_ws_msg(data=data))
                task.add_done_callback(self._log_task_exception)
            except exceptions.ConnectionClosed:
                if self._log:
                    self._log.warning(f"WebSocket connection to node {self._identifier} closed")

                self._session_id = None
                self._available = False

                # Record connection failure in health monitor
                self._health_monitor.record_failure()

                first_disconnect = not self._dispatched_disconnect
                self._dispatched_disconnect = True

                if first_disconnect:
                    # Dispatch node disconnected event
                    player_count = self.player_count
                    disconnected_event = NodeDisconnectedEvent(
                        self._identifier, self._is_nodelink, player_count
                    )
                    disconnected_event.dispatch(self._bot)

                    # If fallback is enabled, switch players to another node
                    # Otherwise, destroy them
                    if self._fallback and self.player_count > 0:
                        await self._handle_node_switch()
                    elif self.player_count > 0:
                        for _player in self.players.copy().values():
                            self._loop.create_task(_player.destroy())

                # Close the websocket if it's not already closed
                if self._websocket and self._websocket.state is not State.CLOSED:
                    self._loop.create_task(self._websocket.close())

                retry = self._backoff.delay()
                if self._log:
                    self._log.warning(
                        f"Retrying connection to Node {self._identifier} in {retry:.1f} secs",
                    )

                # Dispatch node reconnecting event
                event = NodeReconnectingEvent(self._identifier, self._is_nodelink, retry)
                event.dispatch(self._bot)

                await asyncio.sleep(retry)

                if not self.is_connected:
                    if not self._enabled:
                        if self._log:
                            self._log.info(
                                f"Node {self._identifier} is disabled, stopping reconnection."
                            )
                        return
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

    async def _handle_ws_msg(self, data: dict[str, Any]) -> None:
        if self._log:
            self._log.debug(f"Recieved raw payload from Node {self._identifier} with data {data}")
        op = data.get("op", None)

        if op == "stats":
            self._stats = NodeStats(data)
            return

        if op == "ready":
            old_session_id = self._session_id
            self._session_id = data["sessionId"]
            self._last_session_id = self._session_id

            if self._log:
                self._log.info(f"Node {self._identifier} ready with session {self._session_id}")

            if old_session_id != self._session_id:
                if self._log:
                    self._log.info(
                        f"Session ID changed from {old_session_id} to {self._session_id}, updating players"
                    )
                for _player in self._players.copy().values():
                    _player._refresh_endpoint_uri(self._session_id)

            self._available = True
            await self._configure_resuming()

            if self._is_nodelink:
                try:
                    stats_data = await self.send(
                        method="GET",
                        path="stats",
                        include_version=True,
                        ignore_if_available=True,
                    )
                    if stats_data:
                        self._stats = NodeStats(stats_data)
                        if self._log:
                            self._log.debug(
                                f"Initial stats retrieved: players={self._stats.players_total}"
                            )
                except Exception as e:
                    if self._log:
                        self._log.warning(f"Failed to fetch initial stats: {e}")

        if not "guildId" in data:
            return

        player: Player | None = self._players.get(int(data["guildId"]))
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
        guild_id: int | str | None = None,
        query: str | None = None,
        data: dict[str, Any] | str | None = None,
        ignore_if_available: bool = False,
    ) -> Any:
        if not ignore_if_available and not self._available:
            raise NodeNotAvailable(
                f"The node '{self._identifier}' is unavailable.",
            )

        if self._session is None:
            raise NodeNotAvailable(
                f"The node '{self._identifier}' has no active HTTP session; call connect() first.",
            )

        if not ignore_if_available and not self._session_id and "sessions/" in path:
            if self._log:
                self._log.warning(
                    f"No session ID available for node {self._identifier}, waiting for reconnection"
                )
            raise NodeNotAvailable(
                f"The node '{self._identifier}' has no active session.",
            )

        if query:
            query = query.replace("noReplace=False", "noReplace=false")
            query = query.replace("noReplace=True", "noReplace=true")

        uri: str = (
            f"{self._rest_uri}/"
            f"{'v4/' if include_version else ''}"
            f"{path}"
            f"{f'/{guild_id}' if guild_id else ''}"
            f"{f'?{query}' if query else ''}"
        )

        if data and self._is_nodelink and isinstance(data, dict):
            if "encodedTrack" in data and "track" not in data:
                data["track"] = {
                    "encoded": data["encodedTrack"] if data["encodedTrack"] is not None else None
                }
                del data["encodedTrack"]
            if data.get("endTime") is None:
                data.pop("endTime", None)

        request_kwargs: dict[str, Any] = {
            "method": method,
            "url": uri,
            "headers": self._headers,
        }
        if data is not None:
            request_kwargs["json"] = data

        try:
            resp = await self._session.request(**request_kwargs)

            if self._log:
                self._log.debug(
                    f"Making REST request to Node {self._identifier} with method {method} to {uri}",
                )

            if resp.status >= 300:
                resp_data: dict[str, Any] = await resp.json()

                if resp.status == 404 and "session" in resp_data.get("message", "").lower():
                    if self._log:
                        self._log.warning(
                            f"Session not found error from {self._identifier}, marking as unavailable and closing websocket"
                        )
                    self._available = False
                    self._session_id = None
                    # Close websocket to trigger reconnection loop
                    if self._websocket and self._websocket.state is not State.CLOSED:
                        self._loop.create_task(self._websocket.close())

                raise NodeRestException(
                    f"Error from Node {self._identifier} fetching from Lavalink REST api: {resp.status} {resp.reason}: {resp_data.get('message', resp_data)}",
                )

            if method == "DELETE" or resp.status == 204:
                if self._log:
                    self._log.debug(
                        f"REST request to Node {self._identifier} with method {method} to {uri} completed sucessfully and returned no data.",
                    )
                return None

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

        except aiohttp.ContentTypeError as e:
            if self._log:
                self._log.error(
                    f"Node {self._identifier} returned a non-JSON response for {method} {uri}: {e}"
                )
            raise NodeRestException(
                f"Node {self._identifier} returned a non-JSON response: {e}"
            ) from e

        except aiohttp.ClientError as e:
            if self._log:
                self._log.error(
                    f"HTTP client error when connecting to {self._identifier}: {e}, closing websocket to trigger reconnection"
                )
            self._available = False
            # Close websocket to trigger reconnection loop
            if self._websocket and self._websocket.state is not State.CLOSED:
                self._loop.create_task(self._websocket.close())
            raise NodeNotAvailable(f"HTTP error connecting to node {self._identifier}: {e}")

    def get_player(self, guild_id: int) -> Player | None:
        """Takes a guild ID as a parameter. Returns a lyra Player object or None."""
        return self._players.get(guild_id, None)

    async def connect(self, *, reconnect: bool = False) -> Node:
        """Opens a websocket connection to this node. Use `NodePool.create_node()` to
        create and register a node — this only handles the connection itself."""
        await self._bot.wait_until_ready()

        start = time.perf_counter()

        if not self._enabled:
            if self._log:
                self._log.info(f"Node {self._identifier} is disabled, skipping connection.")
            return self

        created_session = False
        if not self._session:
            # Configure connection pooling for optimal concurrent request performance
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connection limit
                limit_per_host=30,  # Per-host connection limit
                ttl_dns_cache=300,  # DNS cache TTL in seconds
            )
            timeout = aiohttp.ClientTimeout(
                total=self._total_timeout, connect=self._connect_timeout
            )
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
            )
            created_session = True

        try:
            if not reconnect:
                try:
                    version: str = await self.send(
                        method="GET",
                        path="version",
                        ignore_if_available=True,
                        include_version=False,
                    )

                    info: dict[str, Any] = await self.send(
                        method="GET",
                        path="info",
                        ignore_if_available=True,
                        include_version=True,
                    )
                except (NodeNotAvailable, NodeRestException) as e:
                    raise NodeConnectionFailure(
                        f"Failed to establish initial connection to node '{self._identifier}': {e}",
                    ) from e

                if info.get("isNodelink", False):
                    self._is_nodelink = True

                await self._handle_version_check(version=version)

                if self._log:
                    self._log.debug(
                        f"Version check from Node {self._identifier} successful. Returned version {version}",
                    )

            # Note: _session_id and _available are already reset in _listen()
            # before calling connect(reconnect=True), so no redundant reset needed here

            headers = dict(self._headers)
            if self._resume_key and self._last_session_id:
                headers["Session-Id"] = self._last_session_id

            self._websocket = await ws_connect(
                f"{self._websocket_uri}/v4/websocket",
                additional_headers=headers,
                ping_interval=self._heartbeat,
            )

            if not self._websocket:
                raise NodeConnectionFailure(
                    f"The websocket connection to node '{self._identifier}' failed.",
                )

            if reconnect:
                if self._log:
                    self._log.info(f"Successfully reconnected to Node {self._identifier}")

            if self._log:
                self._log.debug(
                    f"Node {self._identifier} successfully connected to websocket using {self._websocket_uri}/v4/websocket",
                )

            self._dispatched_disconnect = False

            if not self._task or self._task.done():
                self._task = self._loop.create_task(self._listen())

            end = time.perf_counter()

            # Dispatch node connected event
            event = NodeConnectedEvent(self._identifier, self._is_nodelink, reconnect)
            event.dispatch(self._bot)

            # Record successful connection in health monitor
            if not reconnect:
                self._health_monitor.record_success()

            if self._log:
                self._log.info(f"Connected to node {self._identifier}. Took {end - start:.3f}s")
            return self

        except (aiohttp.ClientConnectorError, OSError, ConnectionRefusedError) as e:
            self._health_monitor.record_failure()
            if created_session and self._session and not self._session.closed:
                await self._session.close()
                self._session = None
            raise NodeConnectionFailure(
                f"The connection to node '{self._identifier}' failed: {e}",
            ) from None
        except exceptions.InvalidHandshake as e:
            self._health_monitor.record_failure()
            if created_session and self._session and not self._session.closed:
                await self._session.close()
                self._session = None
            raise NodeConnectionFailure(
                f"The password for node '{self._identifier}' is invalid: {e}",
            ) from None
        except exceptions.InvalidURI as e:
            self._health_monitor.record_failure()
            if created_session and self._session and not self._session.closed:
                await self._session.close()
                self._session = None
            raise NodeConnectionFailure(
                f"The URI for node '{self._identifier}' is invalid: {e}",
            ) from None
        except Exception:
            self._health_monitor.record_failure()
            if created_session and self._session and not self._session.closed:
                await self._session.close()
                self._session = None
            raise

    async def disconnect(self) -> None:
        """Disconnects a connected Lavalink or NodeLink node and removes it from the node pool.
        This also destroys any players connected to the node.
        """

        start = time.perf_counter()

        player_count = self.player_count

        for player in self.players.copy().values():
            await player.destroy()
            if self._log:
                self._log.debug("All players disconnected from node.")

        self._available = False
        self._latency_cache = None

        if not self._dispatched_disconnect:
            self._dispatched_disconnect = True
            NodeDisconnectedEvent(self._identifier, self._is_nodelink, player_count).dispatch(
                self._bot
            )

        if self._task:
            self._task.cancel()

        if self._latency_task:
            self._latency_task.cancel()

        if self._websocket and self._websocket.state is not State.CLOSED:
            try:
                await self._websocket.close()
            except Exception as e:
                if self._log:
                    self._log.debug(f"Error closing websocket during disconnect: {e}")
        if self._session and not getattr(self._session, "closed", True):
            try:
                await self._session.close()
            except Exception as e:
                if self._log:
                    self._log.debug(f"Error closing http session during disconnect: {e}")
        if self._log:
            self._log.debug("Websocket and http session closed.")

        self._pool._nodes.pop(self._identifier, None)

        end = time.perf_counter()
        if self._log:
            self._log.info(
                f"Successfully disconnected from node {self._identifier} and closed all sessions. Took {end - start:.3f}s",
            )

    async def build_track(self, identifier: str, ctx: ContextType | None = None) -> Track:
        """
        Builds a track using a valid track identifier

        You can also pass in a discord.py Context object to get a
        Context object on the track it builds.
        """

        data: dict[str, Any] = await self.send(
            method="GET",
            path="decodetrack",
            query=f"encodedTrack={quote(identifier)}",
        )

        track_info = data["info"]

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
        ctx: ContextType | None = None,
        search_type: SearchType | None = SearchType.ytsearch,
        filters: list[Filter] | None = None,
    ) -> Playlist | list[Track] | None:
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
                and not path.exists(query)
            ):
                query = f"{search_type}:{query}"

        # Capture YouTube timestamp if present
        if (match := URLRegex.YOUTUBE_TIMESTAMP.match(query)) and match.group("time"):
            timestamp = float(match.group("time"))

        # Make request to Lavalink
        data = await self.send(
            method="GET",
            path="loadtracks",
            query=f"identifier={quote(query)}",
        )

        load_type = data.get("loadType")
        data_type = "data"

        if not load_type:
            raise TrackLoadError(
                "There was an error while trying to load this track.",
            )

        elif load_type in ("LOAD_FAILED", "error"):
            exception = data.get("data") or data.get("exception") or {}
            raise TrackLoadError(
                f"{exception.get('message', 'Unknown error')} "
                f"[{exception.get('severity', 'unknown')}]",
            )

        elif load_type in ("NO_MATCHES", "empty"):
            return None

        elif load_type in ("PLAYLIST_LOADED", "playlist"):
            track_list = data[data_type]["tracks"]
            playlist_info = data[data_type]["info"]

            tracks = [
                Track(
                    track_id=track["encoded"],
                    info=track["info"],
                    ctx=ctx,
                    track_type=TrackType(track["info"]["sourceName"]),
                    filters=filters,
                    timestamp=timestamp,
                )
                for track in track_list
            ]

            if not tracks:
                return None

            return Playlist(
                playlist_info=playlist_info,
                tracks=tracks,
                playlist_type=PlaylistType(tracks[0].track_type.value),
                thumbnail=tracks[0].thumbnail,
                uri=query,
            )

        elif load_type in ("SEARCH_RESULT", "TRACK_LOADED", "track", "search", "episode"):
            if isinstance(data[data_type], dict):
                data[data_type] = [data[data_type]]

            # Handle local files
            if path.exists(query):
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

        elif load_type in ("album", "artist", "station", "podcast", "show"):
            track_list = data[data_type]["tracks"]
            playlist_info = data[data_type]["info"]
            tracks = [
                Track(
                    track_id=t["encoded"],
                    info=t["info"],
                    ctx=ctx,
                    track_type=TrackType(t["info"]["sourceName"]),
                    filters=filters,
                    timestamp=timestamp,
                )
                for t in track_list
            ]
            if not tracks:
                return None
            return Playlist(
                playlist_info=playlist_info,
                tracks=tracks,
                playlist_type=PlaylistType(tracks[0].track_type.value),
                thumbnail=tracks[0].thumbnail,
                uri=query,
            )

        else:
            raise TrackLoadError(
                "There was an error while trying to load this track.",
            )

    async def get_recommendations(
        self,
        *,
        track: Track,
        ctx: ContextType | None = None,
    ) -> list[Track] | Playlist | None:
        """
        Gets recommendations for a track.

        In Lavalink v4, recommendations are handled by plugins.
        For Spotify/Deezer/Tidal/JioSaavn tracks, use the matching '\\*rec:' search prefix.
        For YouTube tracks, use the autoplay/radio playlist.

        Args:
            track: The track to get recommendations for
            ctx: Discord context for recommended tracks

        Returns:
            The recommended tracks, as list[Track] or Playlist depending on the source.

        Raises:
            TrackLoadError: If the track's source doesn't support recommendations.
        """
        if track is None:
            raise TypeError("get_recommendations() requires a track, got None.")

        if track.track_type in (TrackType.YOUTUBE, TrackType.YOUTUBE_MUSIC):
            return await self.get_tracks(
                query=f"https://www.youtube.com/watch?v={track.identifier}&list=RD{track.identifier}",
                search_type=SearchType.ytsearch,
                ctx=ctx,
            )

        search_type = self._RECOMMENDATION_SEARCH_TYPES.get(track.track_type)
        if search_type is None:
            raise TrackLoadError(
                "Recommendations are only supported for Spotify, Deezer, Tidal, "
                "JioSaavn, and YouTube tracks. Make sure the appropriate plugins "
                "are installed on your Lavalink or NodeLink server.",
            )

        return await self.get_tracks(
            query=track.identifier,
            search_type=search_type,
            ctx=ctx,
        )

    async def load_search(
        self,
        *,
        query: str,
        types: list[LavaSearchType],
        search_type: SearchType | None = None,
        ctx: ContextType | None = None,
    ) -> SearchResult | None:
        """
        Searches for tracks, albums, artists, playlists, and text using the LavaSearch plugin.

        This method is a convenience wrapper around SearchManager.load_search().
        For more details, see the SearchManager class documentation.

        Args:
            query: The search query string
            types: List of search types (track, album, artist, playlist, text)
            search_type: Optional search platform (ytsearch, ytmsearch, scsearch, spsearch, amsearch, etc.)
            ctx: Discord context for the search

        Returns:
            SearchResult object containing the search results, or None if no results found
        """
        return await self._search_manager.load_search(
            query=query,
            types=types,
            search_type=search_type,
            ctx=ctx,
        )


class _NodePoolMeta(type):
    @property
    def nodes(cls) -> dict[str, Node]:
        return cast("type[NodePool]", cls)._nodes

    @property
    def node_count(cls) -> int:
        return len(cast("type[NodePool]", cls)._nodes)

    def __repr__(cls) -> str:
        return f"<Lyra.NodePool node_count={cls.node_count}>"


class NodePool(metaclass=_NodePoolMeta):
    """The base class for the node pool.
    This holds all the nodes that are to be used by the bot.
    """

    __slots__ = ()
    _nodes: ClassVar[dict[str, Node]] = {}

    @classmethod
    def get_best_node(cls, *, algorithm: NodeAlgorithm) -> Node:
        """Fetches the best node based on an NodeAlgorithm.
        This option is preferred if you want to choose the best node
        from a multi-node setup using either the node's latency,
        player count, or overall health score.

        Use NodeAlgorithm.by_ping if you want to get the best node
        based on the node's latency.

        Use NodeAlgorithm.by_total_players if you want to get the best node
        based on how many total players it has. This method will return a node with
        the least amount of total players.

        Use NodeAlgorithm.by_playing_players if you want to get the best node
        based on how many players are currently playing. This method will return a node
        with the least amount of actively playing players. This is more accurate than
        by_total_players as it only considers players that are actively playing.

        Use NodeAlgorithm.by_health if you want to get the best node
        based on overall health score (latency, uptime, load, stability).
        This is recommended for production multi-node setups.
        """
        available_nodes: list[Node] = [node for node in cls._nodes.values() if node._available]

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
            tested_nodes: dict[Node, float] = {node: node.latency for node in nodes_to_consider}
            reachable_nodes: dict[Node, float] = {
                node: latency for node, latency in tested_nodes.items() if latency >= 0
            }
            if reachable_nodes:
                tested_nodes = reachable_nodes
            best_latency = min(tested_nodes.values())
            best_nodes = [node for node, lat in tested_nodes.items() if lat == best_latency]
            return random.choice(best_nodes)

        elif algorithm == NodeAlgorithm.by_total_players:
            # Use the total players count from node stats
            tested_nodes: dict[Node, float] = {
                node: node.stats.players_total for node in nodes_to_consider
            }
            return min(tested_nodes, key=tested_nodes.__getitem__)

        elif algorithm == NodeAlgorithm.by_playing_players:
            # Use the playing players count from node stats
            tested_nodes: dict[Node, float] = {
                node: node.stats.players_active for node in nodes_to_consider
            }
            return min(tested_nodes, key=tested_nodes.__getitem__)

        elif algorithm == NodeAlgorithm.by_health:
            # Higher health score is better
            tested_nodes: dict[Node, float] = {
                node: node.health_score for node in nodes_to_consider
            }
            return max(tested_nodes, key=tested_nodes.__getitem__)

        else:
            raise ValueError(
                "The algorithm provided is not a valid NodeAlgorithm.",
            )

    @classmethod
    def get_node(cls, *, identifier: str | None = None) -> Node:
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

        if identifier not in available_nodes:
            raise NoNodesAvailable(
                f"Node '{identifier}' is not available.",
            )

        return available_nodes[identifier]

    @classmethod
    async def create_node(
        cls,
        *,
        bot: BotType,
        host: str,
        port: int,
        password: str,
        identifier: str,
        enabled: bool = True,
        secure: bool = False,
        heartbeat: int = 120,
        resume_key: str | None = None,
        resume_timeout: int = 60,
        loop: asyncio.AbstractEventLoop | None = None,
        session: aiohttp.ClientSession | None = None,
        lyrics: bool = False,
        search: bool = False,
        fallback: bool = False,
        logger: logging.Logger | None = None,
        circuit_breaker_threshold: int = 5,
        circuit_timeout: float = 60.0,
        connect_timeout: float = 10.0,
        total_timeout: float = 30.0,
    ) -> Node:
        """Creates a Node object to be then added into the node pool.

        In Lavalink v4, platform support (Spotify, Apple Music, etc.) is handled
        by server-side plugins. Configure these in your Lavalink server's
        application.yml file instead of passing credentials to the client.

        See docs/hdi/pool.md for the full parameter reference.

        Health Monitor Parameters:
            circuit_breaker_threshold (int): Number of consecutive failures before circuit opens. Default: 5
                For foreign/unstable nodes, consider increasing to 10-20.
            circuit_timeout (float): Seconds to keep circuit open before retry. Default: 60.0
                For foreign nodes, consider increasing to 120.0 or more.

        Connection Timeout Parameters:
            connect_timeout (float): Timeout in seconds for establishing connection. Default: 10.0
                For foreign nodes with high latency, consider increasing to 30.0-60.0.
            total_timeout (float): Total timeout in seconds for all operations. Default: 30.0
                For foreign nodes, consider increasing to 60.0-120.0.
        """
        if identifier in cls._nodes:
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
            enabled=enabled,
            secure=secure,
            heartbeat=heartbeat,
            resume_key=resume_key,
            resume_timeout=resume_timeout,
            loop=loop,
            session=session,
            lyrics=lyrics,
            search=search,
            fallback=fallback,
            logger=logger,
            circuit_breaker_threshold=circuit_breaker_threshold,
            circuit_timeout=circuit_timeout,
            connect_timeout=connect_timeout,
            total_timeout=total_timeout,
        )

        await node.connect()
        cls._nodes[node._identifier] = node
        return node

    @classmethod
    async def disconnect(cls) -> None:
        """Disconnects all nodes from the node pool."""

        for node in list(cls._nodes.values()):
            await node.disconnect()
