from __future__ import annotations

import re
from typing import TYPE_CHECKING
from urllib.parse import quote

from .compat import ContextType
from .enums import LavaSearchType, PlaylistType, SearchType, TrackType, URLRegex
from .exceptions import NodeRestException
from .objects import Playlist, Track

if TYPE_CHECKING:
    from .pool import Node

__all__ = ("SearchManager", "SearchResult", "Text")


class Text:
    """The text search result object returned by LavaSearch plugin.
    Represents a text-based search suggestion or result.
    """

    __slots__ = ("plugin_info", "text")

    def __init__(self, *, text: str, plugin_info: dict | None = None):
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
        "albums",
        "artists",
        "playlists",
        "plugin_info",
        "texts",
        "tracks",
    )

    def __init__(
        self,
        *,
        tracks: list[Track] | None = None,
        albums: list[Playlist] | None = None,
        artists: list[Playlist] | None = None,
        playlists: list[Playlist] | None = None,
        texts: list[Text] | None = None,
        plugin_info: dict | None = None,
    ):
        self.tracks: list[Track] = tracks or []
        self.albums: list[Playlist] = albums or []
        self.artists: list[Playlist] = artists or []
        self.playlists: list[Playlist] = playlists or []
        self.texts: list[Text] = texts or []
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
        types: list[LavaSearchType],
        search_type: SearchType | None = None,
        ctx: ContextType | None = None,
    ) -> SearchResult | None:
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
            NodeRestException: If the LavaSearch plugin is not installed or there was an API error
            ValueError: If no search types are specified

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
