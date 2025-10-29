from __future__ import annotations

import re
from typing import TYPE_CHECKING, List, Optional
from urllib.parse import quote

from discord import ApplicationContext

from .enums import LavaSearchType, PlaylistType, SearchType, TrackType, URLRegex
from .exceptions import NodeRestException, TrackLoadError
from .objects import Playlist, Track

if TYPE_CHECKING:
    from .pool import Node

__all__ = ("SearchManager", "Text", "SearchResult")


class Text:
    """The text search result object returned by LavaSearch plugin.
    Represents a text-based search suggestion or result.
    """

    __slots__ = ("text", "plugin_info")

    def __init__(self, *, text: str, plugin_info: Optional[dict] = None):
        self.text: str = text
        self.plugin_info: dict = plugin_info or {}

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"<Lyra.text text={self.text!r}>"


class SearchResult:
    """The search result object returned by LavaSearch plugin.
    Contains tracks, albums, artists, playlists, and text results from a search query.
    """

    __slots__ = (
        "tracks",
        "albums",
        "artists",
        "playlists",
        "texts",
        "plugin_info",
    )

    def __init__(
        self,
        *,
        tracks: Optional[List[Track]] = None,
        albums: Optional[List[Playlist]] = None,
        artists: Optional[List[Playlist]] = None,
        playlists: Optional[List[Playlist]] = None,
        texts: Optional[List["Text"]] = None,
        plugin_info: Optional[dict] = None,
    ):
        self.tracks: List[Track] = tracks or []
        self.albums: List[Playlist] = albums or []
        self.artists: List[Playlist] = artists or []
        self.playlists: List[Playlist] = playlists or []
        self.texts: List[Text] = texts or []
        self.plugin_info: dict = plugin_info or {}

    def __repr__(self) -> str:
        return (
            f"<Lyra.search_result "
            f"tracks={len(self.tracks)} "
            f"albums={len(self.albums)} "
            f"artists={len(self.artists)} "
            f"playlists={len(self.playlists)} "
            f"texts={len(self.texts)}>"
        )


class SearchManager:
    """Manager class for LavaSearch plugin functionality.

    This class handles search operations for tracks, albums, artists, playlists,
    and text using the LavaSearch plugin on a Lavalink server.
    """

    __slots__ = ("_node",)

    def __init__(self, node: Node):
        """Initialize the SearchManager with a node.

        Args:
            node: The Node instance to use for search operations
        """
        self._node = node

    async def load_search(
        self,
        *,
        query: str,
        types: List[LavaSearchType],
        search_type: Optional[SearchType] = None,
        ctx: Optional[ApplicationContext] = None,
    ) -> Optional[SearchResult]:
        """
        Searches for tracks, albums, artists, playlists, and text using the LavaSearch plugin.

        This method requires the LavaSearch plugin to be installed on your Lavalink server.
        See https://github.com/topi314/LavaSearch for installation instructions.

        Args:
            query: The search query string
            types: List of search types (track, album, artist, playlist, text)
            search_type: Optional search platform (ytsearch, ytmsearch, scsearch, spsearch, amsearch, etc.)
                        If not provided, uses the default search platform configured in Lavalink
            ctx: Discord context for the search

        Returns:
            SearchResult object containing the search results, or None if no results found

        Raises:
            TrackLoadError: If there was an error loading the search results
            NodeRestException: If the LavaSearch plugin is not installed or there was an API error

        Example:
            ```python
            # Search YouTube for tracks and albums
            result = await search_manager.load_search(
                query="architects animals",
                types=[LavaSearchType.TRACK, LavaSearchType.ALBUM],
                search_type=SearchType.ytsearch,
                ctx=ctx
            )

            # Search Spotify
            result = await search_manager.load_search(
                query="metallica",
                types=[LavaSearchType.TRACK, LavaSearchType.ARTIST],
                search_type=SearchType.spsearch,
                ctx=ctx
            )

            if result:
                print(f"Found {len(result.tracks)} tracks")
                print(f"Found {len(result.albums)} albums")
            ```
        """
        # Check if LavaSearch is enabled for this node
        if not self._node._search_enabled:
            raise NodeRestException(
                "LavaSearch is not enabled for this node. "
                "Set search=True when creating the node to enable this feature."
            )

        if not types:
            raise ValueError("At least one search type must be specified")

        # Apply search prefix if search_type is provided
        # Similar to get_tracks() method
        if (
            search_type
            and not URLRegex.BASE_URL.match(query)
            and not re.match(r"(?:[a-z]+?)search:.", query)
        ):
            query = f"{search_type}:{query}"

        # Convert types list to comma-separated string
        types_str = ",".join(str(t) for t in types)

        # Make request to LavaSearch endpoint
        try:
            data = await self._node.send(
                method="GET",
                path="loadsearch",
                query=f"query={quote(query)}&types={types_str}",
            )
        except NodeRestException as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise NodeRestException(
                    "LavaSearch plugin is not installed on the Lavalink server. "
                    "Please install it from https://github.com/topi314/LavaSearch"
                ) from e
            raise

        # Check for empty response (204 No Content)
        if not data:
            return None

        # Parse tracks
        tracks = []
        if "tracks" in data:
            tracks = [
                Track(
                    track_id=track["encoded"],
                    info=track["info"],
                    ctx=ctx,
                    track_type=TrackType(track["info"]["sourceName"]),
                )
                for track in data["tracks"]
            ]

        # Parse albums
        albums = []
        if "albums" in data:
            albums = [
                Playlist(
                    playlist_info=album["info"],
                    tracks=[],  # Albums don't include tracks in search results
                    playlist_type=PlaylistType.OTHER,
                )
                for album in data["albums"]
            ]

        # Parse artists
        artists = []
        if "artists" in data:
            artists = [
                Playlist(
                    playlist_info=artist["info"],
                    tracks=[],  # Artists don't include tracks in search results
                    playlist_type=PlaylistType.OTHER,
                )
                for artist in data["artists"]
            ]

        # Parse playlists
        playlists = []
        if "playlists" in data:
            playlists = [
                Playlist(
                    playlist_info=playlist["info"],
                    tracks=[],  # Playlists don't include tracks in search results
                    playlist_type=PlaylistType.OTHER,
                )
                for playlist in data["playlists"]
            ]

        # Parse text results
        texts = []
        if "texts" in data:
            texts = [
                Text(
                    text=text["text"],
                    plugin_info=text.get("plugin", {}),
                )
                for text in data["texts"]
            ]

        return SearchResult(
            tracks=tracks,
            albums=albums,
            artists=artists,
            playlists=playlists,
            texts=texts,
            plugin_info=data.get("plugin", {}),
        )
