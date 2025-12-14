from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any, Optional, Tuple

from discord import Bot, Guild

from .enums import MixEndReason
from .lyrics import LyricLine, Lyrics
from .objects import Track

if TYPE_CHECKING:
    from .player import Player

__all__ = (
    "LyraEvent",
    "TrackStartEvent",
    "TrackEndEvent",
    "TrackStuckEvent",
    "TrackExceptionEvent",
    "WebSocketClosedPayload",
    "WebSocketClosedEvent",
    "WebSocketOpenEvent",
    "LyricsFoundEvent",
    "LyricsNotFoundEvent",
    "LyricsLineEvent",
    "NodeConnectedEvent",
    "NodeDisconnectedEvent",
    "NodeReconnectingEvent",
    "PlayerCreatedEvent",
    "VolumeChangedEvent",
    "PlayerConnectedEvent",
    "FiltersChangedEvent",
    "PauseEvent",
    "SeekEvent",
    "MixStartedEvent",
    "MixEndedEvent",
)


class LyraEvent(ABC):
    """The base class for all events dispatched by a node.
    Every event must be formatted within your bot's code as a listener.
    i.e: If you want to listen for when a track starts, the event would be:
    ```py
    @bot.listen
    async def on_lyra_track_start(self, event):
    ```
    """

    name = "event"
    handler_args: Tuple

    def dispatch(self, bot: Bot) -> None:
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

    def __init__(self, data: dict, player: Player):
        self.player: Player = player
        self.track: Optional[Track] = self.player._current

        # on_lyra_track_start(player, track)
        self.handler_args = self.player, self.track

    def __repr__(self) -> str:
        return f"<Lyra.TrackStartEvent player={self.player!r} track={self.track!r}>"


class TrackEndEvent(LyraEvent):
    """Fired when a track has successfully ended.
    Returns the player associated with the event along with the lyra.Track object and reason.
    """

    name = "track_end"

    __slots__ = ("player", "track", "reason")

    def __init__(self, data: dict, player: Player):
        self.player: Player = player
        self.track: Optional[Track] = self.player._ending_track
        self.reason: str = data["reason"]

        # on_lyra_track_end(player, track, reason)
        self.handler_args = self.player, self.track, self.reason

    def __repr__(self) -> str:
        return (
            f"<Lyra.TrackEndEvent player={self.player!r} track_id={self.track!r} "
            f"reason={self.reason!r}>"
        )


class TrackStuckEvent(LyraEvent):
    """Fired when a track is stuck and cannot be played. Returns the player
    associated with the event along with the lyra.Track object
    to be further parsed by the end user.
    """

    name = "track_stuck"

    __slots__ = ("player", "track", "threshold")

    def __init__(self, data: dict, player: Player):
        self.player: Player = player
        self.track: Optional[Track] = self.player._ending_track
        self.threshold: float = data["thresholdMs"]

        # on_lyra_track_stuck(player, track, threshold)
        self.handler_args = self.player, self.track, self.threshold

    def __repr__(self) -> str:
        return (
            f"<Lyra.TrackStuckEvent player={self.player!r} track={self.track!r} "
            f"threshold={self.threshold!r}>"
        )


class TrackExceptionEvent(LyraEvent):
    """Fired when a track error has occured.
    Returns the player associated with the event along with the error code and exception.
    """

    name = "track_exception"

    __slots__ = ("player", "track", "exception")

    def __init__(self, data: dict, player: Player):
        self.player: Player = player
        self.track: Optional[Track] = self.player._ending_track
        # Error is for Lavalink <= 3.3
        self.exception: str = data.get(
            "error",
            "",
        ) or data.get("exception", "")

        # on_lyra_track_exception(player, track, error)
        self.handler_args = self.player, self.track, self.exception

    def __repr__(self) -> str:
        return f"<Lyra.TrackExceptionEvent player={self.player!r} exception={self.exception!r}>"


class WebSocketClosedPayload:
    __slots__ = ("code", "reason", "by_remote", "_guild_id", "_bot")

    def __init__(self, data: dict, bot: Optional[Bot] = None):
        self._bot: Optional[Bot] = bot
        self._guild_id: int = int(data["guildId"])
        self.code: int = data["code"]
        self.reason: str = data["reason"]
        self.by_remote: bool = data["byRemote"]

    @property
    def guild(self) -> Optional[Guild]:
        """Returns the guild associated with this event.
        Lazily fetches the guild to avoid circular imports.
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
    """Fired when a websocket connection to a node has been closed.
    Returns the reason and the error code.
    """

    name = "websocket_closed"

    __slots__ = ("payload",)

    def __init__(self, data: dict, player: Any) -> None:
        # Extract bot from player to avoid circular import with NodePool
        bot = getattr(player, "_bot", None)
        self.payload: WebSocketClosedPayload = WebSocketClosedPayload(data, bot)

        # on_lyra_websocket_closed(payload)
        self.handler_args = (self.payload,)

    def __repr__(self) -> str:
        return f"<Lyra.WebsocketClosedEvent payload={self.payload!r}>"


class WebSocketOpenEvent(LyraEvent):
    """Fired when a websocket connection to a node has been initiated.
    Returns the target and the session SSRC.
    """

    name = "websocket_open"

    __slots__ = ("target", "ssrc")

    def __init__(self, data: dict, _: Any) -> None:
        self.target: str = data["target"]
        self.ssrc: int = data["ssrc"]

        # on_lyra_websocket_open(target, ssrc)
        self.handler_args = self.target, self.ssrc

    def __repr__(self) -> str:
        return f"<Lyra.WebsocketOpenEvent target={self.target!r} ssrc={self.ssrc!r}>"


class LyricsFoundEvent(LyraEvent):
    """Event triggered when lyrics are found"""

    name = "lyrics_found"

    __slots__ = ("player", "track", "lyrics")

    def __init__(self, data: dict, player: Player):
        self.player: Player = player
        self.track: Optional[Track] = player._current
        self.lyrics: Lyrics = Lyrics(data)

        # on_lyra_lyrics_found(player, track, lyrics)
        self.handler_args = self.player, self.track, self.lyrics

    def __repr__(self) -> str:
        return f"<Lyra.LyricsFoundEvent player={self.player!r} track={self.track!r} lyrics={self.lyrics!r}>"


class LyricsNotFoundEvent(LyraEvent):
    """Event triggered when lyrics are not found"""

    name = "lyrics_not_found"

    __slots__ = ("player", "track")

    def __init__(self, data: dict, player: Player):
        self.player: Player = player
        self.track: Optional[Track] = player._current

        # on_lyra_lyrics_unavailable(player, track)
        self.handler_args = self.player, self.track

    def __repr__(self) -> str:
        return f"<Lyra.LyricsNotFoundEvent player={self.player!r} track={self.track!r}>"


class LyricsLineEvent(LyraEvent):
    """Event triggered when lyrics move to a new line"""

    name = "lyrics_line"

    __slots__ = ("player", "track", "line")

    def __init__(self, data: dict, player: Player):
        self.player: Player = player
        self.track: Optional[Track] = player._current

        # Create a lyric line object
        line_data = data.get("line", {})
        self.line: LyricLine = LyricLine(
            text=line_data.get("line", ""),
            time=line_data.get("timestamp", 0) / 1000.0,
            duration=line_data.get("duration"),
        )

        # on_lyra_lyrics_update(player, track, line)
        self.handler_args = self.player, self.track, self.line

    def __repr__(self) -> str:
        return f"<Lyra.LyricsLineEvent player={self.player!r} line={self.line!r}>"


class NodeConnectedEvent(LyraEvent):
    """Fired when a node successfully connects to Lavalink.
    Returns the node identifier and whether this is a reconnection.
    """

    name = "node_connected"

    __slots__ = ("node_id", "is_nodelink", "reconnect")

    def __init__(self, node_id: str, is_nodelink: bool, reconnect: bool = False):
        self.node_id: str = node_id
        self.is_nodelink: bool = is_nodelink
        self.reconnect: bool = reconnect

        # on_lyra_node_connected(node_id, is_nodelink, reconnect)
        self.handler_args = self.node_id, self.is_nodelink, self.reconnect

    def __repr__(self) -> str:
        return f"<Lyra.NodeConnectedEvent node_id={self.node_id!r} is_nodelink={self.is_nodelink!r} reconnect={self.reconnect!r}>"


class NodeDisconnectedEvent(LyraEvent):
    """Fired when a node disconnects from Lavalink.
    Returns the node identifier and the number of players that were affected.
    """

    name = "node_disconnected"

    __slots__ = ("node_id", "is_nodelink", "player_count")

    def __init__(self, node_id: str, is_nodelink: bool, player_count: int):
        self.node_id: str = node_id
        self.is_nodelink: bool = is_nodelink
        self.player_count: int = player_count

        # on_lyra_node_disconnected(node_id, is_nodelink, player_count)
        self.handler_args = self.node_id, self.is_nodelink, self.player_count

    def __repr__(self) -> str:
        return f"<Lyra.NodeDisconnectedEvent node_id={self.node_id!r} is_nodelink={self.is_nodelink!r} player_count={self.player_count!r}>"


class NodeReconnectingEvent(LyraEvent):
    """Fired when a node is attempting to reconnect to Lavalink.
    Returns the node identifier and the retry delay in seconds.
    """

    name = "node_reconnecting"

    __slots__ = ("node_id", "is_nodelink", "retry_in")

    def __init__(self, node_id: str, is_nodelink: bool, retry_in: float):
        self.node_id: str = node_id
        self.is_nodelink: bool = is_nodelink
        self.retry_in: float = retry_in

        # on_lyra_node_reconnecting(node_id, is_nodelink, retry_in)
        self.handler_args = self.node_id, self.is_nodelink, self.retry_in

    def __repr__(self) -> str:
        return f"<Lyra.NodeReconnectingEvent node_id={self.node_id!r} is_nodelink={self.is_nodelink!r} retry_in={self.retry_in!r}>"


class PlayerCreatedEvent(LyraEvent):
    """Fired when a player is created (NodeLink specific)"""

    name = "player_created"

    __slots__ = ("player", "guild_id")

    def __init__(self, data: dict, player: Player):
        self.player: Player = player
        self.guild_id: int = int(data.get("guildId", 0))

        # on_lyra_player_created(player, guild_id)
        self.handler_args = self.player, self.guild_id

    def __repr__(self) -> str:
        return f"<Lyra.PlayerCreatedEvent player={self.player!r} guild_id={self.guild_id!r}>"


class VolumeChangedEvent(LyraEvent):
    """Fired when player volume is changed (NodeLink specific)"""

    name = "volume_changed"

    __slots__ = ("player", "volume")

    def __init__(self, data: dict, player: Player):
        self.player: Player = player
        self.volume: int = data.get("volume", 100)

        # on_lyra_volume_changed(player, volume)
        self.handler_args = self.player, self.volume

    def __repr__(self) -> str:
        return f"<Lyra.VolumeChangedEvent player={self.player!r} volume={self.volume!r}>"


class PlayerConnectedEvent(LyraEvent):
    """Fired when a player connects to Discord voice (NodeLink specific)"""

    name = "player_connected"

    __slots__ = ("player", "voice")

    def __init__(self, data: dict, player: Player):
        self.player: Player = player
        self.voice: dict = data.get("voice", {})

        # on_lyra_player_connected(player, voice)
        self.handler_args = self.player, self.voice

    def __repr__(self) -> str:
        return f"<Lyra.PlayerConnectedEvent player={self.player!r} voice={self.voice!r}>"


class FiltersChangedEvent(LyraEvent):
    """Fired when player filters are changed (NodeLink specific)"""

    name = "filters_changed"

    __slots__ = ("player", "filters")

    def __init__(self, data: dict, player: Player):
        self.player: Player = player
        self.filters: dict = data.get("filters", {})

        # on_lyra_filters_changed(player, filters)
        self.handler_args = self.player, self.filters

    def __repr__(self) -> str:
        return f"<Lyra.FiltersChangedEvent player={self.player!r} filters={self.filters!r}>"


class PauseEvent(LyraEvent):
    """Fired when player is paused (NodeLink specific)"""

    name = "pause"
    __slots__ = ("player", "paused")

    def __init__(self, data: dict, player: Player):
        self.player: Player = player
        self.paused: bool = data.get("paused", True)
        self.handler_args = self.player, self.paused

    def __repr__(self) -> str:
        return f"<Lyra.PauseEvent player={self.player!r} paused={self.paused!r}>"


class SeekEvent(LyraEvent):
    """Fired when player seeks (NodeLink specific)"""

    name = "seek"
    __slots__ = ("player", "position")

    def __init__(self, data: dict, player: Player):
        self.player: Player = player
        self.position: int = data.get("position", 0)
        self.handler_args = self.player, self.position

    def __repr__(self) -> str:
        return f"<Lyra.SeekEvent player={self.player!r} position={self.position!r}>"


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
        track: The track being mixed in
        volume: Volume level of the mix layer (0.0 - 1.0)
    """

    name = "mix_started"
    __slots__ = ("player", "mix_id", "track", "volume")

    def __init__(self, data: dict, player: Player):
        self.player: Player = player
        self.mix_id: str = data.get("mixId", "")
        self.volume: float = data.get("volume", 1.0)

        # Parse track data if present
        track_data = data.get("track")
        if track_data:
            self.track: Optional[Track] = Track(track_data)
        else:
            self.track: Optional[Track] = None

        # on_lyra_mix_started(player, mix_id, track, volume)
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
    __slots__ = ("player", "mix_id", "reason")

    def __init__(self, data: dict, player: Player):
        self.player: Player = player
        self.mix_id: str = data.get("mixId", "")
        self.reason: str = data.get("reason", MixEndReason.FINISHED)

        # on_lyra_mix_ended(player, mix_id, reason)
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
