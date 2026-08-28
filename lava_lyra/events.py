from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any

from .compat import BotType, GuildType
from .enums import MixEndReason, TrackType
from .lyrics import LyricLine, Lyrics
from .objects import Track

if TYPE_CHECKING:
    from .player import Player


__all__ = (
    "FiltersChangedEvent",
    "LyraEvent",
    "LyricsFoundEvent",
    "LyricsLineEvent",
    "LyricsNotFoundEvent",
    "MixEndedEvent",
    "MixStartedEvent",
    "NodeConnectedEvent",
    "NodeDisconnectedEvent",
    "NodeReconnectingEvent",
    "PauseEvent",
    "PlayerConnectedEvent",
    "PlayerCreatedEvent",
    "SeekEvent",
    "SponsorBlockSegmentSkippedEvent",
    "SponsorBlockSegmentsLoadedEvent",
    "TrackEndEvent",
    "TrackExceptionEvent",
    "TrackExceptionPayload",
    "TrackStartEvent",
    "TrackStuckEvent",
    "VolumeChangedEvent",
    "WebSocketClosedEvent",
    "WebSocketClosedPayload",
)


class LyraEvent(ABC):
    """The base class for all events dispatched by a node.

    Every event must be formatted within your bot's code as a listener.
    For example, to listen for when a track starts. Each event's
    `handler_args` determine the positional arguments your listener
    receives — for `on_lyra_track_start`, that's `(player, track)`.

    py-cord::

        @bot.listen()
        async def on_lyra_track_start(player, track):
            pass

    discord.py::

        @bot.event
        async def on_lyra_track_start(player, track):
            pass
    """

    __slots__ = ("handler_args",)

    name = "event"
    handler_args: tuple[Any, ...]

    def dispatch(self, bot: BotType) -> None:
        bot.dispatch(f"lyra_{self.name}", *self.handler_args)


class TrackStartEvent(LyraEvent):
    """Fired when a track has successfully started.
    Returns the player associated with the event and the lyra.Track object.
    """

    name = "track_start"

    __slots__ = (
        "player",
        "track",
    )

    def __init__(self, data: dict[str, Any], player: Player):
        self.player: Player = player
        self.track: Track | None = self.player._current

        self.handler_args = self.player, self.track

    def __repr__(self) -> str:
        return f"<Lyra.TrackStartEvent player={self.player!r} track={self.track!r}>"


class TrackEndEvent(LyraEvent):
    """Fired when a track has successfully ended.
    Returns the player associated with the event along with the lyra.Track object and reason.
    """

    name = "track_end"

    __slots__ = ("player", "reason", "track")

    def __init__(self, data: dict[str, Any], player: Player):
        self.player: Player = player
        self.track: Track | None = self.player._ending_track
        self.reason: str = data.get("reason", "")

        self.handler_args = self.player, self.track, self.reason

    def __repr__(self) -> str:
        return (
            f"<Lyra.TrackEndEvent player={self.player!r} "
            f"track_id={self.track.track_id if self.track else None!r} reason={self.reason!r}>"
        )


class TrackStuckEvent(LyraEvent):
    """Fired when a track is stuck and cannot be played. Returns the player
    associated with the event along with the lyra.Track object and the
    threshold in milliseconds that was exceeded.
    """

    name = "track_stuck"

    __slots__ = ("player", "threshold", "track")

    def __init__(self, data: dict[str, Any], player: Player):
        self.player: Player = player
        self.track: Track | None = self.player._ending_track
        self.threshold: float = data.get("thresholdMs", 0)

        self.handler_args = self.player, self.track, self.threshold

    def __repr__(self) -> str:
        return (
            f"<Lyra.TrackStuckEvent player={self.player!r} track={self.track!r} "
            f"threshold={self.threshold!r}>"
        )


class TrackExceptionPayload:
    """Exception details from a `TrackExceptionEvent`: `message`, Lavalink's
    `severity` classification (`COMMON`/`SUSPICIOUS`/`FAULT`), and the
    underlying `cause`, when Lavalink provides one.
    """

    __slots__ = ("cause", "message", "severity")

    def __init__(
        self,
        message: str,
        severity: str | None = None,
        cause: str | None = None,
    ) -> None:
        self.message: str = message
        self.severity: str | None = severity
        self.cause: str | None = cause

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"<Lyra.TrackExceptionPayload message={self.message!r} severity={self.severity!r}>"


class TrackExceptionEvent(LyraEvent):
    """Fired when a track error has occurred.
    Returns the player associated with the event along with the track and a
    TrackExceptionPayload describing the message, severity, and cause.
    """

    name = "track_exception"

    __slots__ = ("exception", "player", "track")

    def __init__(self, data: dict[str, Any], player: Player):
        self.player: Player = player
        self.track: Track | None = self.player._ending_track
        raw_exception = data.get("exception") or data.get("error") or ""
        if isinstance(raw_exception, dict):
            self.exception: TrackExceptionPayload = TrackExceptionPayload(
                message=raw_exception.get("message", "Unknown error"),
                severity=raw_exception.get("severity"),
                cause=raw_exception.get("cause"),
            )
        else:
            self.exception = TrackExceptionPayload(message=str(raw_exception))

        self.handler_args = self.player, self.track, self.exception

    def __repr__(self) -> str:
        return f"<Lyra.TrackExceptionEvent player={self.player!r} exception={self.exception!r}>"


class WebSocketClosedPayload:
    """Details from a `WebSocketClosedEvent`. `guild` is resolved lazily
    from the bot's cache on access, and is `None` if uncached.
    `by_remote` is whether Discord's voice servers closed the connection.
    """

    __slots__ = ("_bot", "_guild_id", "by_remote", "code", "reason")

    def __init__(self, data: dict[str, Any], bot: BotType | None = None):
        self._bot: BotType | None = bot
        self._guild_id: int = int(data.get("guildId") or 0)
        self.code: int = data.get("code") or 0
        self.reason: str = data.get("reason") or ""
        self.by_remote: bool = bool(data.get("byRemote"))

    @property
    def guild(self) -> GuildType | None:
        """Returns the guild associated with this event, resolved lazily
        from the bot's cache. Returns `None` if uncached.
        """
        if self._bot is None:
            return None
        return self._bot.get_guild(self._guild_id)

    def __repr__(self) -> str:
        return (
            f"<Lyra.WebSocketClosedPayload guild={self.guild!r} code={self.code!r} "
            f"reason={self.reason!r} by_remote={self.by_remote!r}>"
        )


class WebSocketClosedEvent(LyraEvent):
    """Fired when the Discord voice websocket for a guild has been closed
    (relayed by the node, not the node's own connection).
    Returns a WebSocketClosedPayload with the guild, close code, reason,
    and whether the close was remote.
    """

    name = "websocket_closed"

    __slots__ = ("payload",)

    def __init__(self, data: dict[str, Any], player: Any) -> None:
        # Extract bot from player to avoid circular import with NodePool
        bot = getattr(player, "_bot", None)
        self.payload: WebSocketClosedPayload = WebSocketClosedPayload(data, bot)

        self.handler_args = (self.payload,)

    def __repr__(self) -> str:
        return f"<Lyra.WebSocketClosedEvent payload={self.payload!r}>"


class LyricsFoundEvent(LyraEvent):
    """Event triggered when lyrics are found"""

    name = "lyrics_found"

    __slots__ = ("lyrics", "player", "track")

    def __init__(self, data: dict[str, Any], player: Player):
        self.player: Player = player
        self.track: Track | None = player._current
        self.lyrics: Lyrics = Lyrics(data)

        self.handler_args = self.player, self.track, self.lyrics

    def __repr__(self) -> str:
        return f"<Lyra.LyricsFoundEvent player={self.player!r} track={self.track!r} lyrics={self.lyrics!r}>"


class LyricsNotFoundEvent(LyraEvent):
    """Event triggered when lyrics are not found"""

    name = "lyrics_not_found"

    __slots__ = ("player", "track")

    def __init__(self, data: dict[str, Any], player: Player):
        self.player: Player = player
        self.track: Track | None = player._current

        self.handler_args = self.player, self.track

    def __repr__(self) -> str:
        return f"<Lyra.LyricsNotFoundEvent player={self.player!r} track={self.track!r}>"


class LyricsLineEvent(LyraEvent):
    """Event triggered when lyrics move to a new line"""

    name = "lyrics_line"

    __slots__ = ("line", "line_index", "player", "skipped", "track")

    def __init__(self, data: dict[str, Any], player: Player):
        self.player: Player = player
        self.track: Track | None = player._current

        line_data: dict[str, Any] = data.get("line", {})
        if not isinstance(line_data, dict):
            line_data = {}
        text = line_data.get("line")
        if text is None:
            text = line_data.get("text") or ""
        raw_duration = line_data.get("duration")
        self.line: LyricLine = LyricLine(
            text=text,
            time=(line_data.get("timestamp", line_data.get("time", 0)) or 0) / 1000.0,
            duration=(raw_duration / 1000.0) if raw_duration else None,
        )
        self.line_index: int | None = data.get("lineIndex")
        self.skipped: bool = bool(data.get("skipped", False))

        self.handler_args = self.player, self.track, self.line

    def __repr__(self) -> str:
        return f"<Lyra.LyricsLineEvent player={self.player!r} line={self.line!r}>"


class NodeConnectedEvent(LyraEvent):
    """Fired when a node successfully connects to Lavalink or NodeLink.
    Returns the node identifier, whether the node is a NodeLink instance,
    and whether this is a reconnection.
    """

    name = "node_connected"

    __slots__ = ("is_nodelink", "node_id", "reconnect")

    def __init__(self, node_id: str, is_nodelink: bool, reconnect: bool = False):
        self.node_id: str = node_id
        self.is_nodelink: bool = is_nodelink
        self.reconnect: bool = reconnect

        self.handler_args = self.node_id, self.is_nodelink, self.reconnect

    def __repr__(self) -> str:
        return f"<Lyra.NodeConnectedEvent node_id={self.node_id!r} is_nodelink={self.is_nodelink!r} reconnect={self.reconnect!r}>"


class NodeDisconnectedEvent(LyraEvent):
    """Fired when a node disconnects from Lavalink or NodeLink.
    Returns the node identifier, whether the node is a NodeLink instance,
    and the number of players that were affected.
    """

    name = "node_disconnected"

    __slots__ = ("is_nodelink", "node_id", "player_count")

    def __init__(self, node_id: str, is_nodelink: bool, player_count: int):
        self.node_id: str = node_id
        self.is_nodelink: bool = is_nodelink
        self.player_count: int = player_count

        self.handler_args = self.node_id, self.is_nodelink, self.player_count

    def __repr__(self) -> str:
        return f"<Lyra.NodeDisconnectedEvent node_id={self.node_id!r} is_nodelink={self.is_nodelink!r} player_count={self.player_count!r}>"


class NodeReconnectingEvent(LyraEvent):
    """Fired when a node is attempting to reconnect to Lavalink or NodeLink.
    Returns the node identifier, whether the node is a NodeLink instance,
    and the retry delay in seconds.
    """

    name = "node_reconnecting"

    __slots__ = ("is_nodelink", "node_id", "retry_in")

    def __init__(self, node_id: str, is_nodelink: bool, retry_in: float):
        self.node_id: str = node_id
        self.is_nodelink: bool = is_nodelink
        self.retry_in: float = retry_in

        self.handler_args = self.node_id, self.is_nodelink, self.retry_in

    def __repr__(self) -> str:
        return f"<Lyra.NodeReconnectingEvent node_id={self.node_id!r} is_nodelink={self.is_nodelink!r} retry_in={self.retry_in!r}>"


class PlayerCreatedEvent(LyraEvent):
    """Fired when a player is created (NodeLink specific)"""

    name = "player_created"

    __slots__ = ("guild_id", "player")

    def __init__(self, data: dict[str, Any], player: Player):
        self.player: Player = player
        self.guild_id: int = int(data.get("guildId", 0))

        self.handler_args = self.player, self.guild_id

    def __repr__(self) -> str:
        return f"<Lyra.PlayerCreatedEvent player={self.player!r} guild_id={self.guild_id!r}>"


class VolumeChangedEvent(LyraEvent):
    """Fired when player volume is changed (NodeLink specific)"""

    name = "volume_changed"

    __slots__ = ("player", "volume")

    def __init__(self, data: dict[str, Any], player: Player):
        self.player: Player = player
        self.volume: int = data.get("volume", 100)

        self.handler_args = self.player, self.volume

    def __repr__(self) -> str:
        return f"<Lyra.VolumeChangedEvent player={self.player!r} volume={self.volume!r}>"


class PlayerConnectedEvent(LyraEvent):
    """Fired when a player connects to Discord voice (NodeLink specific)"""

    name = "player_connected"

    __slots__ = ("player", "voice")

    def __init__(self, data: dict[str, Any], player: Player):
        self.player: Player = player
        self.voice: dict[str, Any] = data.get("voice", {})

        self.handler_args = self.player, self.voice

    def __repr__(self) -> str:
        return f"<Lyra.PlayerConnectedEvent player={self.player!r} voice={self.voice!r}>"


class FiltersChangedEvent(LyraEvent):
    """Fired when player filters are changed (NodeLink specific)"""

    name = "filters_changed"

    __slots__ = ("filters", "player")

    def __init__(self, data: dict[str, Any], player: Player):
        self.player: Player = player
        self.filters: dict[str, Any] = data.get("filters", {})

        self.handler_args = self.player, self.filters

    def __repr__(self) -> str:
        return f"<Lyra.FiltersChangedEvent player={self.player!r} filters={self.filters!r}>"


class PauseEvent(LyraEvent):
    """Fired when the player is paused or resumed (NodeLink specific)"""

    name = "pause"
    __slots__ = ("paused", "player")

    def __init__(self, data: dict[str, Any], player: Player):
        self.player: Player = player
        self.paused: bool = data.get("paused", True)
        self.handler_args = self.player, self.paused

    def __repr__(self) -> str:
        return f"<Lyra.PauseEvent player={self.player!r} paused={self.paused!r}>"


class SeekEvent(LyraEvent):
    """Fired when player seeks (NodeLink specific)"""

    name = "seek"
    __slots__ = ("player", "position")

    def __init__(self, data: dict[str, Any], player: Player):
        self.player: Player = player
        self.position: int = data.get("position", 0)
        self.handler_args = self.player, self.position

    def __repr__(self) -> str:
        return f"<Lyra.SeekEvent player={self.player!r} position={self.position!r}>"


class SponsorBlockSegmentsLoadedEvent(LyraEvent):
    name = "sponsorblock_segments_loaded"
    __slots__ = ("player", "segments")

    def __init__(self, data: dict[str, Any], player: Player):
        self.player: Player = player
        self.segments: list[dict[str, Any]] = data.get("segments", [])

        self.handler_args = self.player, self.segments

    def __repr__(self) -> str:
        return f"<Lyra.SponsorBlockSegmentsLoadedEvent player={self.player!r} segments={self.segments!r}>"


class SponsorBlockSegmentSkippedEvent(LyraEvent):
    name = "sponsorblock_segment_skipped"
    __slots__ = ("player", "segment", "track")

    def __init__(self, data: dict[str, Any], player: Player):
        self.player: Player = player
        self.track: Track | None = player._current
        self.segment: dict[str, Any] = data.get("segment", {})

        self.handler_args = self.player, self.track, self.segment

    def __repr__(self) -> str:
        return f"<Lyra.SponsorBlockSegmentSkippedEvent player={self.player!r} segment={self.segment!r}>"


class MixStartedEvent(LyraEvent):
    """Event fired when a mix layer starts (NodeLink specific)

    A mix layer is an additional audio stream that plays alongside the main track.
    This is useful for features like:
    - Background music
    - Sound effects
    - Audio overlays
    - Multi-track playback

    Attributes:
        player: The player instance
        mix_id: Unique identifier for this mix layer
        track: The track being mixed in (or None)
        volume: Volume level of the mix layer (0.0 - 1.0)
    """

    name = "mix_started"
    __slots__ = ("mix_id", "player", "track", "volume")

    def __init__(self, data: dict[str, Any], player: Player):
        self.player: Player = player
        self.mix_id: str = data.get("mixId", "")
        self.volume: float = data.get("volume", 1.0)

        # Parse track data if present
        track_data = data.get("track")
        if track_data and isinstance(track_data, dict):
            track_info: dict[str, Any] = track_data.get("info") or {}
            self.track: Track | None = Track(
                track_id=track_data.get("encoded", ""),
                info=track_info,
                track_type=TrackType(track_info.get("sourceName", "other")),
            )
        else:
            self.track = None

        self.handler_args = (self.player, self.mix_id, self.track, self.volume)

    def __repr__(self) -> str:
        return (
            f"<Lyra.MixStartedEvent "
            f"player={self.player!r} "
            f"mix_id={self.mix_id!r} "
            f"track={self.track!r} "
            f"volume={self.volume!r}>"
        )


class MixEndedEvent(LyraEvent):
    """Event fired when a mix layer ends (NodeLink specific)

    This event is triggered when a mix layer stops playing, either because:
    - It finished playing naturally (FINISHED)
    - It was manually removed (REMOVED)
    - An error occurred (ERROR)
    - The main track ended (MAIN_ENDED)

    Attributes:
        player: The player instance
        mix_id: Unique identifier for this mix layer
        reason: Why the mix ended (see MixEndReason)
    """

    name = "mix_ended"
    __slots__ = ("mix_id", "player", "reason")

    def __init__(self, data: dict[str, Any], player: Player):
        self.player: Player = player
        self.mix_id: str = data.get("mixId", "")
        self.reason: MixEndReason = MixEndReason(data.get("reason", "FINISHED"))

        self.handler_args = (self.player, self.mix_id, self.reason)

    @property
    def is_finished(self) -> bool:
        """Check if mix ended naturally"""
        return self.reason == MixEndReason.FINISHED

    @property
    def is_removed(self) -> bool:
        """Check if mix was manually removed"""
        return self.reason == MixEndReason.REMOVED

    @property
    def is_error(self) -> bool:
        """Check if mix ended due to error"""
        return self.reason == MixEndReason.ERROR

    @property
    def is_main_ended(self) -> bool:
        """Check if mix ended because main track ended"""
        return self.reason == MixEndReason.MAIN_ENDED

    def __repr__(self) -> str:
        return (
            f"<Lyra.MixEndedEvent "
            f"player={self.player!r} "
            f"mix_id={self.mix_id!r} "
            f"reason={self.reason!r}>"
        )
