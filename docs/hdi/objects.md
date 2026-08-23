# Use the Track and Playlist objects

`Player.get_tracks()`, `Node.get_tracks()`, and `Node.load_search()` all hand you back `Track`
and/or `Playlist` objects. This page covers the attributes you'll actually use day to day.

## The Track object

The `Track` object has the following attributes:

:::{list-table}
:header-rows: 1

* - Attribute
  - Type
  - Description

* - `title`
  - `str`
  - The track's title.

* - `author`
  - `str`
  - The track's author/uploader.

* - `uri`
  - `str`
  - The track's playback URI.

* - `identifier`
  - `str`
  - The source-specific identifier for the track (e.g. a YouTube video ID).

* - `isrc`
  - `Optional[str]`
  - The track's ISRC code, if the source provides one.

* - `thumbnail`
  - `Optional[str]`
  - A thumbnail/artwork URL for the track, if available.

* - `length`
  - `int`
  - The track's length in milliseconds.

* - `position`
  - `int`
  - The track's playback position in milliseconds at the time it was built (usually `0`).

* - `is_stream`
  - `bool`
  - Whether the track is a livestream.

* - `is_seekable`
  - `bool`
  - Whether the track supports seeking.

* - `track_type`
  - `TrackType`
  - Which source the track came from (`TrackType.YOUTUBE`, `TrackType.SPOTIFY`, etc.).

* - `playlist`
  - `Optional[Playlist]`
  - The `Playlist` this track belongs to, if it was loaded as part of one.

* - `requester`
  - `Optional[Member | User | ClientUser]`
  - Whoever requested the track, if a `ctx` was supplied when the track was built/searched.

* - `filters`
  - `Optional[List[Filter]]`
  - Per-track filters, set via the `filters` parameter on `get_tracks()`.

* - `track_id`
  - `str`
  - The raw Lavalink/NodeLink track identifier (base64-encoded track data), as used by `Node.build_track()`.

* - `info`
  - `dict`
  - The raw track info payload the track was built from.

* - `original`
  - `Optional[Track]`
  - For most tracks this is the track itself. For Spotify/Apple Music tracks it starts as `None` and is set once the track has been resolved to a playable source via search.

* - `timestamp`
  - `Optional[float]`
  - The `?t=`/`&t=`/`&start=` offset in seconds parsed from a YouTube URL, if present. Used as the initial playback position when the track starts.

* - `ctx`
  - `ContextType | None`
  - The `Context` object supplied when the track was built/searched, if any. Used to derive `requester` when one isn't explicitly passed.

:::

`Track` also supports equality (`==`) based on its underlying track ID, and `str(track)` returns
its title.

## The Playlist object

Returned when a query resolves to a playlist or album (e.g. a Spotify/YouTube playlist URL). The
`Playlist` object has the following attributes:

:::{list-table}
:header-rows: 1

* - Attribute
  - Type
  - Description

* - `name`
  - `str`
  - The playlist's name.

* - `playlist_info`
  - `dict`
  - The raw playlist info payload the playlist was built from.

* - `tracks`
  - `List[Track]`
  - The tracks in the playlist.

* - `track_count`
  - `int`
  - The number of tracks in the playlist.

* - `playlist_type`
  - `PlaylistType`
  - Which source the playlist came from (`PlaylistType.YOUTUBE`, `PlaylistType.SPOTIFY`, etc.), for playlists loaded via `Node.get_tracks()`. Albums, artists, and playlists returned by `Node.load_search()` (LavaSearch) are always `PlaylistType.OTHER` regardless of their actual source — see [](search.md).

* - `selected_track`
  - `Optional[Track]`
  - The track that was selected/highlighted when the playlist URL was loaded (e.g. `&index=` on a YouTube playlist URL), if any.

* - `uri`
  - `Optional[str]`
  - The URI/URL the playlist was loaded from, if one was supplied.

* - `thumbnail`
  - `Optional[str]`
  - The playlist's thumbnail, taken from its first track.

* - `length`
  - `int`
  - The combined length of every track in the playlist, in milliseconds.

:::

`Playlist` also behaves like a sequence of its tracks — you can iterate over it, index into it
(`playlist[0]`), take a slice, check `len(playlist)`, and use `in` to check membership. To remove
and return a track from it, use `Playlist.pop()`:

```py
last_track = playlist.pop()
```

:::{note}

`len(playlist)` and `Playlist.length` are **not** the same thing. `len(playlist)` returns the
**number of tracks** in the playlist (equivalent to `Playlist.track_count`). `Playlist.length`
returns the **combined playback duration** of every track, in milliseconds. Use whichever one
actually matches what you need.

:::

:::{important}

Albums, artists, and playlists returned by `Node.load_search()` do **not** include their tracks
(`tracks` will be empty and `uri`/`thumbnail` won't be set) — only metadata. Refer to
[](search.md) for details.

:::
