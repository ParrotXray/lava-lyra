from __future__ import annotations

import asyncio
import time
from typing import Any, override

from . import events
from .compat import (
    BotType,
    ContextType,
    GuildType,
    GuildVoiceStateType,
    VoiceChannelType,
    VoiceChannelTypes,
    VoiceProtocolType,
    VoiceServerUpdateType,
)
from .enums import SearchType
from .events import LyraEvent, TrackEndEvent, TrackStartEvent
from .exceptions import (
    FilterInvalidArgument,
    FilterTagAlreadyInUse,
    FilterTagInvalid,
    NodelinkExclusive,
    NodeNotAvailable,
    NodeRestException,
    TrackInvalidPosition,
    TrackLoadError,
)
from .filters import Equalizer, Filter, Timescale
from .lyrics import LyricLine, Lyrics, LyricsManager
from .objects import Playlist, Track
from .pool import Node, NodePool
from .utils import LavalinkVersion, voice_field

__all__ = ("Filters", "Player")


class Filters:
    """Helper class for filters"""

    __slots__ = ("_filters",)

    def __init__(self) -> None:
        self._filters: list[Filter] = []

    @property
    def has_preload(self) -> bool:
        """Property which checks if any applied filters were preloaded"""
        return any(f for f in self._filters if f.preload == True)

    @property
    def has_global(self) -> bool:
        """Property which checks if any applied filters are global"""
        return any(f for f in self._filters if f.preload == False)

    @property
    def empty(self) -> bool:
        """Property which checks if the filter list is empty"""
        return len(self._filters) == 0

    def add_filter(self, *, filter: Filter, node: Node) -> None:
        """Adds a filter to the list of filters applied.

        `node` is the Lavalink/Nodelink node the filter would be sent to, and is used
        to reject Nodelink-exclusive filters (see `Filter.nodelink_exclusive`) before
        they can be queued up against a plain Lavalink instance.
        """
        if filter.nodelink_exclusive and not node._is_nodelink:
            raise NodelinkExclusive(
                f"The '{type(filter).__name__}' filter is a Nodelink-exclusive feature "
                "and is not supported on a Lavalink instance",
            )
        if any(f for f in self._filters if f.tag == filter.tag):
            raise FilterTagAlreadyInUse(
                "A filter with that tag is already in use.",
            )
        if any(f for f in self._filters if type(f) is type(filter)):
            raise FilterTagAlreadyInUse(
                "A filter of that type is already applied.",
            )
        self._filters.append(filter)

    def remove_filter(self, *, filter_tag: str) -> None:
        """Removes a filter from the list of filters applied using its filter tag"""
        if not any(f for f in self._filters if f.tag == filter_tag):
            raise FilterTagInvalid("A filter with that tag was not found.")

        for index, filter in enumerate(self._filters):
            if filter.tag == filter_tag:
                del self._filters[index]

    def edit_filter(self, *, filter_tag: str, to_apply: Filter, node: Node) -> None:
        """Edits a filter in the list of filters applied using its filter tag and replaces it with the new filter.

        `node` is the Lavalink/Nodelink node the filter would be sent to, and is used
        to reject Nodelink-exclusive filters (see `Filter.nodelink_exclusive`) before
        they can be queued up against a plain Lavalink instance.
        """
        if to_apply.nodelink_exclusive and not node._is_nodelink:
            raise NodelinkExclusive(
                f"The '{type(to_apply).__name__}' filter is a Nodelink-exclusive feature "
                "and is not supported on a Lavalink instance",
            )
        if not any(f for f in self._filters if f.tag == filter_tag):
            raise FilterTagInvalid("A filter with that tag was not found.")

        for index, filter in enumerate(self._filters):
            if filter.tag == filter_tag:
                if not type(filter) == type(to_apply):
                    raise FilterInvalidArgument(
                        "Edited filter is not the same type as the current filter.",
                    )
                if to_apply.tag != filter_tag:
                    raise FilterInvalidArgument(
                        "Edited filter tag is not the same as the current filter tag.",
                    )
                if self._filters[index] == to_apply:
                    raise FilterInvalidArgument("Edited filter is the same as the current filter.")

                self._filters[index] = to_apply

    def has_filter(self, *, filter_tag: str) -> bool:
        """Checks if a filter exists in the list of filters using its filter tag"""
        return any(f for f in self._filters if f.tag == filter_tag)

    def has_filter_type(self, *, filter_type: Filter) -> bool:
        """Checks if any filters applied match the specified filter type."""
        return any(f for f in self._filters if type(f) == type(filter_type))

    def reset_filters(self) -> None:
        """Removes all filters from the list"""
        self._filters = []

    def get_preload_filters(self) -> list[Filter]:
        """Get all preloaded filters"""
        return [f for f in self._filters if f.preload == True]

    def get_all_payloads(self, node: Node | None = None) -> dict[str, Any]:
        """Returns a formatted dict of all the filter payloads"""
        payload: dict[str, Any] = {}
        for _filter in self._filters:
            if _filter.payload:
                payload.update(_filter.payload)

        if (
            node
            and node._is_nodelink
            and node._version >= LavalinkVersion(3, 7, 0)
            and "compressor" in payload
        ):
            compressor = dict(payload["compressor"])
            if "gain" in compressor:
                compressor["makeupGain"] = compressor.pop("gain")
            if "attack" in compressor:
                compressor["attack"] = compressor["attack"] / 1000
            if "release" in compressor:
                compressor["release"] = compressor["release"] / 1000
            payload["compressor"] = compressor

        supports_transition = (
            node is not None and node._is_nodelink and node._version >= LavalinkVersion(3, 7, 0)
        )

        if "equalizer" in payload:
            eq_filter = next((f for f in self._filters if isinstance(f, Equalizer)), None)

            if supports_transition and eq_filter is not None:
                eq_body: dict[str, Any] = {"bands": payload["equalizer"]}
                if eq_filter.transition is not None:
                    eq_body["transition"] = eq_filter.transition
                payload["equalizer"] = eq_body

        return payload

    def get_filters(self) -> list[Filter]:
        """Returns the current list of applied filters"""
        return self._filters


class Player(VoiceProtocolType):
    """The base player class for Lyra.
    In order to initiate a player, you must pass it in as a cls when you connect to a channel::

        await ctx.author.voice.channel.connect(cls=lava_lyra.Player)
    """

    __slots__ = (
        "_bot",
        "_current",
        "_ending_track",
        "_filters",
        "_guild",
        "_is_connected",
        "_last_position",
        "_last_update_local",
        "_log",
        "_lyrics_manager",
        "_next_track",
        "_node",
        "_paused",
        "_player_endpoint_uri",
        "_voice_state",
        "_volume",
        "channel",
        "client",
    )

    def __init__(
        self,
        client: BotType,
        channel: VoiceChannelType,
        *,
        node: Node | None = None,
    ) -> None:
        self.client = client
        self.channel = channel
        self._guild = channel.guild

        self._bot: BotType = client
        self._node: Node = node if node else NodePool.get_node()
        self._lyrics_manager = LyricsManager(self)
        self._current: Track | None = None
        self._filters: Filters = Filters()
        self._volume: int = 100
        self._paused: bool = False
        self._is_connected: bool = False

        self._last_position: int = 0
        self._last_update_local: float = 0
        self._ending_track: Track | None = None
        self._next_track: Track | None = None
        self._log = self._node._log

        self._voice_state: dict[str, Any] = {}

        self._player_endpoint_uri: str = f"sessions/{self._node._session_id}/players"

    def __repr__(self) -> str:
        return (
            f"<Lyra.player bot={self.bot} guildId={self.guild.id} "
            f"is_connected={self.is_connected} is_playing={self.is_playing}>"
        )

    @property
    def position(self) -> int:
        """Property which returns the player's position in a track in milliseconds"""
        current = self._current
        if not self.is_playing or current is None:
            return 0

        if current.original:
            current = current.original

        if self.is_paused:
            return min(self._last_position, current.length)

        if self._last_update_local == 0:
            return 0

        difference = (time.time() * 1000) - self._last_update_local
        position = self._last_position + difference

        return round(min(position, current.length))

    @property
    def rate(self) -> float:
        """Property which returns the player's current rate"""
        if _filter := next((f for f in self._filters._filters if isinstance(f, Timescale)), None):
            return _filter.speed * _filter.rate
        return 1.0

    @property
    def adjusted_position(self) -> float:
        """Property which returns the player's position in a track in milliseconds adjusted for rate"""
        return self.position / self.rate

    @property
    def adjusted_length(self) -> float:
        """Property which returns the player's track length in milliseconds adjusted for rate"""
        current = self.current
        if not self.is_playing or current is None:
            return 0

        if current.original:
            current = current.original

        return current.length / self.rate

    @property
    def is_playing(self) -> bool:
        """Property which returns whether or not the player has a track loaded and connected.

        This stays True while paused — use `Player.is_paused` to check for that separately.
        """
        return self._is_connected and self._current is not None

    @property
    def is_connected(self) -> bool:
        """Property which returns whether or not the player is connected"""
        return self._is_connected

    @property
    def is_paused(self) -> bool:
        """Property which returns whether or not the player is paused.

        This only checks the connection and paused state, not whether a
        track is currently loaded — see `Player.current` for that.
        """
        return self._is_connected and self._paused

    @property
    def current(self) -> Track | None:
        """Property which returns the currently playing track"""
        return self._current

    @property
    def node(self) -> Node:
        """Property which returns the node the player is connected to"""
        return self._node

    @property
    def guild(self) -> GuildType:
        """Property which returns the guild associated with the player"""
        return self._guild

    @property
    def volume(self) -> int:
        """Property which returns the players current volume"""
        return self._volume

    @property
    def filters(self) -> Filters:
        """Property which returns the helper class for interacting with filters"""
        return self._filters

    @property
    def bot(self) -> BotType:
        """Property which returns the bot associated with this player instance"""
        return self._bot

    @property
    def is_dead(self) -> bool:
        """Returns a bool representing whether the player is dead or not.
        A player is considered dead if it has been destroyed and removed from stored players.
        """
        return self.guild.id not in self._node._players

    @property
    def lyrics(self) -> Lyrics | None:
        """Get the current track's lyrics"""
        return self._lyrics_manager.lyrics

    @property
    def has_lyrics(self) -> bool:
        """Check if lyrics exist"""
        return self._lyrics_manager.has_lyrics

    @property
    def lyrics_loaded(self) -> bool:
        """Check if lyrics have been attempted to load"""
        return self._lyrics_manager.lyrics_loaded

    @property
    def is_subscribed(self) -> bool:
        """Check if subscribed to live lyrics"""
        return self._lyrics_manager.is_subscribed

    # Lyrics-related methods (acting as proxies to LyricsManager)
    async def fetch_lyrics(
        self,
        track: Track | None = None,
        skip_track_source: bool = False,
        lang: str | None = None,
    ) -> Lyrics | None:
        """Fetch lyrics"""
        return await self._lyrics_manager.fetch_lyrics(track, skip_track_source, lang=lang)

    async def subscribe_lyrics(self, skip_track_source: bool = False) -> bool:
        """Subscribe to live lyrics

        Args:
            skip_track_source: Skip track source when searching
        """
        return await self._lyrics_manager.subscribe_lyrics(skip_track_source)

    async def unsubscribe_lyrics(self) -> bool:
        """Unsubscribe from live lyrics"""
        return await self._lyrics_manager.unsubscribe_lyrics()

    def get_current_lyrics_lines(self, range_seconds: float = 5.0) -> list[LyricLine]:
        """Get lyric lines near the current playback position"""
        return self._lyrics_manager.get_current_lyrics_lines(range_seconds)

    def _reset_lyrics(self) -> None:
        """Reset lyrics state"""
        self._lyrics_manager.reset()

    def _adjust_end_time(self) -> str | int | None:
        if self._node._version >= LavalinkVersion(4, 0, 0) or (
            self._node._is_nodelink and self._node._version >= LavalinkVersion(3, 2, 0)
        ):
            return None

        return "0" if not self._node._is_nodelink else 0

    async def _update_state(self, data: dict[str, Any]) -> None:
        state: dict[str, Any] = data.get("state", {})
        self._last_update_local = time.time() * 1000
        self._is_connected = bool(state.get("connected"))
        self._last_position = int(state.get("position", 0))
        if self._log:
            self._log.debug(f"Got player update state with data {state}")

    async def _dispatch_voice_update(self, voice_data: dict[str, Any] | None = None) -> None:
        if {"sessionId", "event"} != self._voice_state.keys():
            return

        state = voice_data or self._voice_state
        event = state["event"]

        data = {
            "token": voice_field(event, "token"),
            "endpoint": voice_field(event, "endpoint"),
            "sessionId": state["sessionId"],
            "channelId": str(self.channel.id) if self.channel else None,  # pyrefly: ignore
        }

        await self._node.send(
            method="PATCH",
            path=self._player_endpoint_uri,
            guild_id=self._guild.id,
            data={"voice": data},
        )

        if self._log:
            self._log.debug(
                f"Dispatched voice update to {data['endpoint']} with data {data}",
            )

    @override
    async def on_voice_server_update(self, data: VoiceServerUpdateType) -> None:
        self._voice_state.update({"event": data})
        await self._dispatch_voice_update(self._voice_state)

    @override
    async def on_voice_state_update(self, data: GuildVoiceStateType) -> None:
        self._voice_state.update({"sessionId": voice_field(data, "session_id")})

        channel_id = voice_field(data, "channel_id")
        if not channel_id:
            await self.disconnect()
            self._voice_state.clear()
            return

        channel = self.guild.get_channel(int(channel_id))

        if self.channel != channel and isinstance(channel, VoiceChannelTypes):
            self.channel = channel

        if not channel:
            await self.disconnect()
            self._voice_state.clear()
            return

        await self._dispatch_voice_update(self._voice_state)

    async def _dispatch_event(self, data: dict[str, Any]) -> None:
        event_type: str = data.get("type", "")
        event_cls = getattr(events, event_type, None)
        if event_cls is None:
            return
        event: LyraEvent = event_cls(data, self)

        if isinstance(event, TrackEndEvent) and event.reason not in (
            "REPLACED",
            "replaced",
        ):
            if self._current is self._ending_track:
                self._current = None

        if isinstance(event, TrackEndEvent) and event.reason == "gapless":
            self._current = self._next_track
            self._next_track = None

        event.dispatch(self._bot)

        if isinstance(event, TrackStartEvent):
            self._ending_track = self._current

        if self._log:
            self._log.debug(f"Dispatched event {data['type']} to player.")

    def _refresh_endpoint_uri(self, session_id: str | None) -> None:
        if session_id:
            old_uri = self._player_endpoint_uri
            self._player_endpoint_uri = f"sessions/{session_id}/players"
            if self._log:
                self._log.debug(
                    f"Updated player endpoint URI from {old_uri} to {self._player_endpoint_uri}"
                )
        else:
            if self._log:
                self._log.warning("Cannot refresh endpoint URI: no session ID provided")

    async def _swap_node(self, *, new_node: Node) -> None:
        """Handle swapping to a new node"""
        data = None
        if self.current:
            data = {
                "position": self.position,
                "track": {"encoded": self.current.track_id},
                "volume": self._volume,
                "paused": self._paused,
                "filters": self.filters.get_all_payloads(self._node)
                if not self.filters.empty
                else None,
            }

        self._node._players.pop(self._guild.id, None)

        old_node = self._node
        self._node = new_node
        self._node._players[self._guild.id] = self

        self._refresh_endpoint_uri(new_node._session_id)

        await self._dispatch_voice_update()

        if data:
            try:
                await self._node.send(
                    method="PATCH",
                    path=self._player_endpoint_uri,
                    guild_id=self._guild.id,
                    data=data,
                )
                if self._log:
                    self._log.info(
                        f"Successfully restored player state on new node {new_node._identifier}"
                    )
            except Exception as e:
                if self._log:
                    self._log.error(f"Failed to restore player state on new node: {e}")

        if self._log:
            self._log.info(
                f"Swapped player from node {old_node._identifier} to {new_node._identifier}"
            )

    async def get_tracks(
        self,
        query: str,
        *,
        ctx: ContextType | None = None,
        search_type: SearchType | None = SearchType.ytsearch,
        filters: list[Filter] | None = None,
    ) -> list[Track] | Playlist | None:
        """Fetches tracks from the node's REST api to parse into Lavalink.

        In Lavalink v4, all platform support is handled by server-side plugins.
        Spotify, Apple Music, Deezer, etc. URLs are passed directly to Lavalink
        which uses plugins like LavaSrc to handle them — no credentials are
        needed in Lyra itself.

        You can pass in a discord.py Context object to get a
        Context object on any track you search.

        You may also pass in a List of filters
        to be applied to your track once it plays.
        """
        return await self._node.get_tracks(query, ctx=ctx, search_type=search_type, filters=filters)

    async def build_track(self, identifier: str, ctx: ContextType | None = None) -> Track:
        """
        Builds a track using a valid track identifier

        You can also pass in a discord.py Context object to get a
        Context object on the track it builds.
        """

        return await self._node.build_track(identifier, ctx=ctx)

    async def get_recommendations(
        self,
        *,
        track: Track,
        ctx: ContextType | None = None,
    ) -> list[Track] | Playlist | None:
        """
        Gets recommendations for a track. Supported for Spotify, Deezer, Tidal, JioSaavn, and
        YouTube/YouTube Music tracks — requires the appropriate plugin on Lavalink servers. Raises
        `TrackLoadError` for unsupported sources. You can pass in a discord.py Context
        object to get a Context object on all tracks that get recommended.
        """
        return await self._node.get_recommendations(track=track, ctx=ctx)

    @override
    async def connect(
        self,
        *,
        timeout: float,
        reconnect: bool,
        self_deaf: bool = False,
        self_mute: bool = False,
    ) -> None:
        await self.guild.change_voice_state(
            channel=self.channel,  # pyrefly: ignore [bad-argument-type]
            self_deaf=self_deaf,
            self_mute=self_mute,
        )
        self._node._players[self.guild.id] = self
        self._is_connected = True

    async def stop(self, *, gapless: bool = False) -> None:
        """Stops the currently playing track."""
        if gapless:
            self._require_nodelink()
        if not gapless:
            self._current = None
        self._next_track = None
        await self._node.send(
            method="PATCH",
            path=self._player_endpoint_uri,
            guild_id=self._guild.id,
            data={"nextTrack" if gapless else "encodedTrack": None},
        )

        if self._log:
            self._log.debug("Player has been stopped.")

    @override
    async def disconnect(self, *, force: bool = False) -> None:
        """Disconnects the player from voice."""
        try:
            await self.guild.change_voice_state(channel=None)
        finally:
            self.cleanup()
            self._is_connected = False
            self.channel = None  # pyrefly: ignore [bad-assignment]

    async def destroy(self) -> None:
        """Disconnects and destroys the player, and runs internal cleanup."""
        try:
            await self.disconnect()
        except AttributeError:
            if self.channel is not None or self.is_connected:
                raise

        self._node._players.pop(self.guild.id, None)
        if self.node.is_connected:
            await self._node.send(
                method="DELETE",
                path=self._player_endpoint_uri,
                guild_id=self._guild.id,
            )

        if self._log:
            self._log.debug("Player has been destroyed.")

    async def play(
        self,
        track: Track,
        *,
        start: int = 0,
        end: int = 0,
        ignore_if_playing: bool = False,
        gapless: bool = False,
    ) -> Track | None:
        """Plays a track. If a Spotify or Apple Music track is passed in, it will be handled accordingly."""

        if gapless:
            self._require_nodelink()

        if not self._node._available or not self._node._session_id:
            if self._log:
                self._log.warning("Node not available, attempting to handle disconnect")
            await asyncio.sleep(1)
            return track

        if start == 0 and track.timestamp:
            start = int(track.timestamp * 1000)
            track.timestamp = None

        # Make sure we've never searched the track before
        if track._search_type and track.original is None:
            # First lets try using the tracks ISRC, every track has one (hopefully)
            try:
                if not track.isrc:
                    raise ValueError("Track has no ISRC")
                isrc_results = await self._node.get_tracks(
                    f"{track._search_type}:{track.isrc}", ctx=track.ctx
                )
                if not isinstance(isrc_results, list) or not isrc_results:
                    raise TrackLoadError("No results for ISRC search")
                search = isrc_results[0]
            except Exception:
                # First method didn't work, lets try just searching it up
                try:
                    title_results = await self._node.get_tracks(
                        f"{track._search_type}:{track.title} - {track.author}",
                        ctx=track.ctx,
                    )
                    if not isinstance(title_results, list) or not title_results:
                        raise TrackLoadError("No results for title search")
                    search = title_results[0]
                except Exception:
                    # The song wasn't able to be found, raise error
                    raise TrackLoadError(
                        "No equivalent track was able to be found.",
                    )

            # Build data based on node type
            if self._node._is_nodelink:
                if gapless:
                    data = {"nextTrack": {"encoded": search.track_id}}
                else:
                    data = {
                        "track": {"encoded": search.track_id},
                        "position": start,
                        "endTime": end if end > 0 else self._adjust_end_time(),
                    }
            else:
                data = {
                    "encodedTrack": search.track_id,
                    "position": start,
                    "endTime": end if end > 0 else self._adjust_end_time(),
                }

            track.original = search
            track.track_id = search.track_id
            # Set track_id for later lavalink searches
        else:
            # Build data based on node type
            if self._node._is_nodelink:
                if gapless:
                    data = {"nextTrack": {"encoded": track.track_id}}
                else:
                    data = {
                        "track": {"encoded": track.track_id},
                        "position": start,
                        "endTime": end if end > 0 else self._adjust_end_time(),
                    }
            else:
                data = {
                    "encodedTrack": track.track_id,
                    "position": start,
                    "endTime": end if end > 0 else self._adjust_end_time(),
                }

        if not gapless:
            self._reset_lyrics()

        if gapless:
            self._next_track = track
        elif not (ignore_if_playing and self.is_playing):
            self._current = track

            self._last_position = start
            self._last_update_local = time.time() * 1000

        if not gapless:
            if self.filters.has_preload:
                for filter in self.filters.get_preload_filters():
                    await self.remove_filter(filter_tag=filter.tag)

            if track.filters and not self.filters.has_global:
                for filter in track.filters:
                    await self.add_filter(_filter=filter)

        try:
            await self._node.send(
                method="PATCH",
                path=self._player_endpoint_uri,
                guild_id=self._guild.id,
                data=data,
                query=f"noReplace={ignore_if_playing}",
            )

            if self._log:
                self._log.debug(
                    f"Playing {track.title} from uri {track.uri} with a length of {track.length}",
                )

        except (NodeNotAvailable, NodeRestException) as e:
            if "session" in str(e).lower() or "404" in str(e):
                if self._log:
                    self._log.warning(f"Session error during play: {e}, attempting recovery")
                await asyncio.sleep(1)

                await self._node.send(
                    method="PATCH",
                    path=self._player_endpoint_uri,
                    guild_id=self._guild.id,
                    data=data,
                    query=f"noReplace={ignore_if_playing}",
                )
            else:
                raise

        return self._current if not gapless else self._next_track

    async def _send_player_request(
        self,
        data: dict[str, Any] | None = None,
        method: str = "PATCH",
        query: str | None = None,
        endpoint_suffix: str | None = None,
    ) -> Any:
        """Auxiliary method for sending player requests, including error handling"""
        guild_id = f"{self._guild.id}/{endpoint_suffix}" if endpoint_suffix else self._guild.id

        try:
            return await self._node.send(
                method=method,
                path=self._player_endpoint_uri,
                guild_id=guild_id,
                data=data,
                query=query,
            )
        except (NodeNotAvailable, NodeRestException) as e:
            if "session" in str(e).lower() or "404" in str(e):
                if self._log:
                    self._log.warning(f"Session error in player request: {e}, attempting recovery")
                await asyncio.sleep(1)

                return await self._node.send(
                    method=method,
                    path=self._player_endpoint_uri,
                    guild_id=guild_id,
                    data=data,
                    query=query,
                )
            else:
                raise

    def _require_nodelink(
        self, min_version: LavalinkVersion | None = None, feature_name: str | None = None
    ) -> None:
        """Guards a NodeLink-exclusive Player method."""
        if not self._node._is_nodelink:
            raise NodelinkExclusive(
                "This is a Nodelink-exclusive feature and is not supported on a Lavalink instance"
            )
        if min_version is not None and self._node._version < min_version:
            version_str = f"{min_version.major}.{min_version.minor}.{min_version.fix}"
            raise NodelinkExclusive(
                f"{feature_name} requires NodeLink {version_str}+. Current node does not support it."
            )

    async def seek(self, position: float) -> float:
        """Seeks to a position, in milliseconds, in the currently playing track."""
        if not self._current or not self._current.original:
            return 0.0

        if position < 0 or position > self._current.original.length:
            raise TrackInvalidPosition(
                "Seek position must be between 0 and the track length",
            )

        position = int(position)
        await self._send_player_request({"position": position})

        self._last_position = position
        self._last_update_local = time.time() * 1000

        if self._log:
            self._log.debug(f"Seeking to {position}.")
        return float(self.position)

    async def set_pause(self, pause: bool) -> bool:
        """Sets the pause state of the currently playing track."""
        await self._send_player_request({"paused": pause})
        self._paused = pause

        if self._log:
            self._log.debug(f"Player has been {'paused' if pause else 'resumed'}.")
        return self._paused

    async def set_volume(self, volume: int) -> int:
        """Sets the volume of the player as an integer. Lavalink accepts values from 0 to 1000."""
        await self._send_player_request({"volume": volume})
        self._volume = volume

        if self._log:
            self._log.debug(f"Player volume has been adjusted to {volume}")
        return self._volume

    async def move_to(self, channel: VoiceChannelType) -> None:
        """Moves the player to a new voice channel."""

        await self.guild.change_voice_state(channel=channel)

        self.channel = channel

        await self._dispatch_voice_update()

    async def add_filter(self, _filter: Filter, fast_apply: bool = False) -> Filters:
        """Adds a filter to the player. Takes a lava_lyra.Filter object.
        This will only work if you are using a version of Lavalink that supports filters.
        If you would like for the filter to apply instantly, set the `fast_apply` arg to `True`.

        (You must have a song playing in order for `fast_apply` to work.)
        """

        self._filters.add_filter(filter=_filter, node=self._node)
        payload = self._filters.get_all_payloads(self._node)
        await self._send_player_request({"filters": payload})

        if self._log:
            self._log.debug(f"Filter has been applied to player with tag {_filter.tag}")
        if fast_apply:
            if self._log:
                self._log.debug("Fast apply passed, now applying filter instantly.")
            await self.seek(self.position)

        return self._filters

    async def remove_filter(self, filter_tag: str, fast_apply: bool = False) -> Filters:
        """Removes a filter from the player. Takes a filter tag.
        This will only work if you are using a version of Lavalink that supports filters.
        If you would like for the filter to apply instantly, set the `fast_apply` arg to `True`.

        (You must have a song playing in order for `fast_apply` to work.)
        """

        self._filters.remove_filter(filter_tag=filter_tag)
        payload = self._filters.get_all_payloads(self._node)
        await self._send_player_request({"filters": payload})
        if self._log:
            self._log.debug(f"Filter has been removed from player with tag {filter_tag}")
        if fast_apply:
            if self._log:
                self._log.debug("Fast apply passed, now removing filter instantly.")
            await self.seek(self.position)

        return self._filters

    async def edit_filter(
        self,
        *,
        filter_tag: str,
        edited_filter: Filter,
        fast_apply: bool = False,
    ) -> Filters:
        """Edits a filter from the player using its filter tag and a new filter of the same type.
        The filter to be replaced must have the same tag as the one you are replacing it with.
        This will only work if you are using a version of Lavalink that supports filters.

        If you would like for the filter to apply instantly, set the `fast_apply` arg to `True`.

        (You must have a song playing in order for `fast_apply` to work.)
        """

        self._filters.edit_filter(filter_tag=filter_tag, to_apply=edited_filter, node=self._node)
        payload = self._filters.get_all_payloads(self._node)
        await self._send_player_request({"filters": payload})
        if self._log:
            self._log.debug(f"Filter with tag {filter_tag} has been edited to {edited_filter!r}")
        if fast_apply:
            if self._log:
                self._log.debug("Fast apply passed, now editing filter instantly.")
            await self.seek(self.position)

        return self._filters

    async def reset_filters(self, *, fast_apply: bool = False) -> None:
        """Removes all currently applied filters entirely (not reset to their defaults — use
        `Filter.reset()` per-filter if that's what you want).
        You must have filters applied in order for this to work.
        If you would like the filters to be removed instantly, set the `fast_apply` arg to `True`.

        (You must have a song playing in order for `fast_apply` to work.)
        """

        if self._filters.empty:
            raise FilterInvalidArgument(
                "You must have filters applied first in order to use this method.",
            )
        self._filters.reset_filters()
        await self._send_player_request({"filters": {}})
        if self._log:
            self._log.debug("All filters have been removed from player.")

        if fast_apply:
            if self._log:
                self._log.debug("Fast apply passed, now removing all filters instantly.")
            await self.seek(self.position)

    async def get_sponsorblock(self) -> dict[str, Any]:
        """Requires NodeLink v3.8.0+"""
        self._require_nodelink(LavalinkVersion(3, 8, 0), "SponsorBlock")

        return await self._send_player_request(method="GET", endpoint_suffix="sponsorblock")

    async def set_sponsorblock(
        self,
        *,
        enabled: bool | None = None,
        categories: list[str] | None = None,
        action_types: list[str] | None = None,
        skip_margin_ms: int | None = None,
    ) -> dict[str, Any]:
        """Requires NodeLink v3.8.0+"""
        self._require_nodelink(LavalinkVersion(3, 8, 0), "SponsorBlock")

        data: dict[str, Any] = {}
        if enabled is not None:
            data["enabled"] = enabled
        if categories is not None:
            data["categories"] = categories
        if action_types is not None:
            data["actionTypes"] = action_types
        if skip_margin_ms is not None:
            data["skipMarginMs"] = skip_margin_ms

        return await self._send_player_request(data, endpoint_suffix="sponsorblock")

    async def set_sponsorblock_segments(self, segments: list[dict[str, Any]]) -> dict[str, Any]:
        """Requires NodeLink v3.8.0+"""
        self._require_nodelink(LavalinkVersion(3, 8, 0), "SponsorBlock")

        return await self._send_player_request(
            {"segments": segments}, method="POST", endpoint_suffix="sponsorblock"
        )

    async def clear_sponsorblock(self) -> None:
        """Requires NodeLink v3.8.0+"""
        self._require_nodelink(LavalinkVersion(3, 8, 0), "SponsorBlock")

        await self._send_player_request(method="DELETE", endpoint_suffix="sponsorblock")
