from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from .player import Player
    from .pool import Node

__all__ = (
    "LyricLine",
    "Lyrics",
    "LyricsManager",
)


@dataclass
class LyricLine:
    """Single line lyric class"""

    text: str
    time: float  # Timestamp (seconds)
    duration: Optional[float] = None

    def __repr__(self) -> str:
        return f"<LyricLine text='{self.text}' time={self.time}>"


class Lyrics:
    """Lyrics class"""

    def __init__(self, data: Optional[dict] = None):
        self.source_name: Optional[str] = None
        self.provider: Optional[str] = None
        self.text: Optional[str] = None
        self.lines: List[LyricLine] = []

        if data:
            lyrics_data = data.get("lyrics", data)
            self.source_name = lyrics_data.get("sourceName")
            self.provider = lyrics_data.get("provider")
            self.text = lyrics_data.get("text")

            # Parse lyric lines
            lines_data = lyrics_data.get("lines", [])
            for line_data in lines_data:
                if isinstance(line_data, dict):
                    lyric_line = LyricLine(
                        text=line_data.get("line", ""),
                        time=line_data.get("timestamp", 0) / 1000.0,  # Convert to seconds
                        duration=line_data.get("duration"),
                    )
                    self.lines.append(lyric_line)

    def __bool__(self) -> bool:
        """Check if lyrics exist"""
        return bool(self.lines)

    def __len__(self) -> int:
        """Return number of lyric lines"""
        return len(self.lines)

    def __iter__(self):
        """Iterate over lyric lines"""
        return iter(self.lines)

    def __repr__(self) -> str:
        return f"<Lyrics provider={self.provider} lines={len(self.lines)}>"

    def get_lyrics_at_time(
        self, time_seconds: float, range_seconds: float = 5.0
    ) -> List[LyricLine]:
        """Get lyrics within specified time range"""
        result = []
        for line in self.lines:
            if abs(line.time - time_seconds) <= range_seconds:
                result.append(line)
        return sorted(result, key=lambda x: x.time)


class LyricsManager:
    """Lyrics manager - handles all lyrics related functionalities"""

    def __init__(self, player: Player):
        self.player = player
        self._lyrics: Optional[Lyrics] = None
        self._lyrics_loaded: bool = False
        self._log = logging.getLogger(__name__)

    @property
    def lyrics(self) -> Optional[Lyrics]:
        """Get lyrics of the current track"""
        return self._lyrics

    @property
    def has_lyrics(self) -> bool:
        """Check if there are lyrics"""
        return self._lyrics is not None and bool(self._lyrics)

    @property
    def lyrics_loaded(self) -> bool:
        """Check if lyrics have been attempted to load"""
        return self._lyrics_loaded

    @property
    def enabled(self) -> bool:
        """Check if lyrics feature is enabled on the node"""
        return getattr(self.player._node, "_lyrics_enabled", True)

    def reset(self) -> None:
        """Reset lyrics state"""
        self._lyrics = None
        self._lyrics_loaded = False
        if self._log:
            self._log.debug("Lyrics state has been reset")

    def update_lyrics(self, data: dict) -> None:
        """Update lyrics data"""
        self._lyrics = Lyrics(data)
        self._lyrics_loaded = True
        if self._log:
            self._log.debug(f"Lyrics updated: {len(self._lyrics.lines)} lines")

    def mark_not_found(self) -> None:
        """Mark lyrics as not found"""
        self._lyrics = None
        self._lyrics_loaded = True
        if self._log:
            self._log.debug("Marked lyrics as not found")

    async def fetch_lyrics(self, track=None, skip_track_source: bool = False) -> Optional[Lyrics]:
        """Fetch lyrics"""
        if not self.enabled:
            if self._log:
                self._log.debug("Lyrics feature is not enabled on this node")
            return None

        target_track = track or self.player._current
        if not target_track:
            return None

        try:
            # Determine API endpoint
            if target_track == self.player._current:
                path = f"{self.player._player_endpoint_uri}/{self.player._guild.id}/track/lyrics"
            else:
                path = "lyrics"

            # Build query parameters
            query_params = []
            if skip_track_source:
                query_params.append("skipTrackSource=true")

            if target_track != self.player._current:
                query_params.append(f"track={target_track.track_id}")

            query = "&".join(query_params) if query_params else None

            # Send request
            data = await self.player._node.send(method="GET", path=path, query=query, guild_id=None)

            if data:
                lyrics = Lyrics(data)
                if target_track == self.player._current:
                    self._lyrics = lyrics
                    self._lyrics_loaded = True
                return lyrics

        except Exception as e:
            if self._log:
                self._log.debug(f"Failed to fetch lyrics: {e}")

        return None

    async def subscribe_lyrics(self, skip_track_source: bool = False) -> bool:
        """Subscribe to live lyrics"""
        if not self.enabled:
            if self._log:
                self._log.debug("Lyrics feature is not enabled on this node")
            return False

        try:
            query = "skipTrackSource=true" if skip_track_source else None

            await self.player._node.send(
                method="POST",
                path=f"{self.player._player_endpoint_uri}/{self.player._guild.id}/lyrics/subscribe",
                query=query,
                guild_id=None,
            )

            if self._log:
                self._log.debug("Subscribed to live lyrics")
            return True

        except Exception as e:
            if self._log:
                self._log.debug(f"Failed to subscribe to live lyrics: {e}")
            return False

    async def unsubscribe_lyrics(self) -> bool:
        """Unsubscribe from live lyrics"""
        if not self.enabled:
            if self._log:
                self._log.debug("Lyrics feature is not enabled on this node")
            return False

        try:
            await self.player._node.send(
                method="DELETE",
                path=f"{self.player._player_endpoint_uri}/{self.player._guild.id}/lyrics/subscribe",
                guild_id=None,
            )

            if self._log:
                self._log.debug("Unsubscribed from live lyrics")
            return True

        except Exception as e:
            if self._log:
                self._log.debug(f"Failed to unsubscribe from live lyrics: {e}")
            return False

    def get_current_lyrics_lines(self, range_seconds: float = 5.0) -> List[LyricLine]:
        """Get lyric lines near the current playback position"""
        if not self.enabled or not self._lyrics or not self.player.is_playing:
            return []

        current_time = self.player.position / 1000.0
        return self._lyrics.get_lyrics_at_time(current_time, range_seconds)
