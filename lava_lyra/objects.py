from __future__ import annotations

from typing import TYPE_CHECKING, overload

from .compat import ClientUserType, ContextType, MemberType, UserType
from .enums import PlaylistType, SearchType, TrackType
from .filters import Filter

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = (
    "Playlist",
    "Track",
)


class Track:
    """The base track object. Returns critical track information needed for parsing by Lavalink.
    You can also pass in ApplicationContext to get a discord.py Context object in your track.
    """

    __slots__ = (
        "_search_type",
        "author",
        "ctx",
        "filters",
        "identifier",
        "info",
        "is_seekable",
        "is_stream",
        "isrc",
        "length",
        "original",
        "playlist",
        "position",
        "requester",
        "thumbnail",
        "timestamp",
        "title",
        "track_id",
        "track_type",
        "uri",
    )

    def __init__(
        self,
        *,
        track_id: str,
        info: dict,
        ctx: ContextType | None = None,
        track_type: TrackType,
        search_type: SearchType = SearchType.ytsearch,
        filters: list[Filter] | None = None,
        timestamp: float | None = None,
        requester: MemberType | UserType | ClientUserType | None = None,
    ):
        self.track_id: str = track_id
        self.info: dict = info
        self.track_type: TrackType = track_type
        self.filters: list[Filter] | None = filters
        self.timestamp: float | None = timestamp

        if self.track_type == TrackType.SPOTIFY or self.track_type == TrackType.APPLE_MUSIC:
            self.original: Track | None = None
        else:
            self.original = self
        self._search_type: SearchType = search_type

        self.playlist: Playlist | None = None

        self.title: str = info.get("title", "Unknown Title")
        self.author: str = info.get("author", "Unknown Author")
        self.uri: str = info.get("uri", "")
        self.identifier: str = info.get("identifier", "")
        self.isrc: str | None = info.get("isrc", None)
        self.thumbnail: str | None = info.get("artworkUrl", None) or info.get("thumbnail", None)

        if not self.thumbnail and self.uri and self.track_type is TrackType.YOUTUBE:
            self.thumbnail = f"https://img.youtube.com/vi/{self.identifier}/mqdefault.jpg"

        self.length: int = info.get("length", 0)
        self.is_stream: bool = info.get("isStream", False)
        self.is_seekable: bool = info.get("isSeekable", False)
        self.position: int = info.get("position", 0)

        self.ctx: ContextType | None = ctx
        self.requester: MemberType | UserType | ClientUserType | None = requester
        if not self.requester and self.ctx:
            self.requester = self.ctx.author

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Track):
            return NotImplemented

        return other.track_id == self.track_id

    def __str__(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return f"<Lyra.track title={self.title!r} uri=<{self.uri!r}> length={self.length}>"


class Playlist:
    """The base playlist object.
    Returns critical playlist information needed for parsing by Lavalink.
    You can also pass in ApplicationContext to get a discord.py Context object in your tracks.
    """

    __slots__ = (
        "_thumbnail",
        "_uri",
        "name",
        "playlist_info",
        "playlist_type",
        "selected_track",
        "track_count",
        "tracks",
    )

    def __init__(
        self,
        *,
        playlist_info: dict,
        tracks: list,
        playlist_type: PlaylistType,
        thumbnail: str | None = None,
        uri: str | None = None,
    ):
        self.playlist_info: dict = playlist_info
        self.tracks: list[Track] = tracks
        self.name: str = playlist_info.get("name", "Unknown Playlist")
        self.playlist_type: PlaylistType = playlist_type

        self._thumbnail: str | None = thumbnail
        self._uri: str | None = uri

        for track in self.tracks:
            track.playlist = self

        self.selected_track: Track | None = None
        if (index := playlist_info.get("selectedTrack", -1)) != -1:
            if 0 <= index < len(self.tracks):
                self.selected_track = self.tracks[index]

        self.track_count: int = len(self.tracks)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Lyra.playlist name={self.name!r} track_count={len(self.tracks)}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Playlist):
            return NotImplemented

        return self.name == other.name and self.tracks == other.tracks

    def __len__(self) -> int:
        return len(self.tracks)

    @overload
    def __getitem__(self, index: int) -> Track: ...

    @overload
    def __getitem__(self, index: slice) -> list[Track]: ...

    def __getitem__(self, index: int | slice) -> Track | list[Track]:
        return self.tracks[index]

    def __iter__(self) -> Iterator[Track]:
        return self.tracks.__iter__()

    def __reversed__(self) -> Iterator[Track]:
        return self.tracks.__reversed__()

    def __contains__(self, item: Track) -> bool:
        return item in self.tracks

    def pop(self, index: int = -1) -> Track:
        return self.tracks.pop(index)

    @property
    def uri(self) -> str | None:
        """Returns either an Apple Music/Spotify URL/URI, or None if its neither of those."""
        return self._uri

    @property
    def thumbnail(self) -> str | None:
        """Returns either an Apple Music/Spotify album/playlist thumbnail, or None if its neither of those."""
        return self._thumbnail

    @property
    def length(self) -> int | None:
        """Returns the total length of all tracks in the playlist in milliseconds."""
        return sum(track.length for track in self.tracks)
