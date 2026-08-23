# Use LavaSearch

Lyra supports the [LavaSearch](https://github.com/topi314/LavaSearch) plugin, which provides rich
search results including tracks, albums, artists, playlists, and text suggestions from a single query.

:::{important}

LavaSearch must be installed on your Lavalink server. See the
[LavaSearch installation guide](https://github.com/topi314/LavaSearch) for instructions.

You must also pass `search=True` when creating your node:

```py
await NodePool.create_node(
    bot=bot,
    host="127.0.0.1",
    port=2333,
    password="youshallnotpass",
    identifier="MAIN",
    search=True,
)
```

:::

## Accessing the SearchManager

`Node` does not expose a `SearchManager` as a public property. Instead, `Node` provides a `load_search()` convenience method that wraps `SearchManager.load_search()`:

```py
node = NodePool.get_node(identifier="MAIN")
result = await node.load_search(query="...", types=[...])
```

You can also check whether search is enabled for a node via `Node.search_enabled`.

## Performing a search

Use `Node.load_search()` to run a rich search query:

```py
from lava_lyra import LavaSearchType, SearchType

result = await node.load_search(
    query="architects animals",
    types=[LavaSearchType.TRACK, LavaSearchType.ALBUM],
    search_type=SearchType.ytsearch,
    ctx=ctx,
)

if result:
    print(f"Tracks found: {len(result.tracks)}")
    print(f"Albums found: {len(result.albums)}")
```

### Parameters

:::{list-table}
:header-rows: 1

* - Name
  - Type
  - Description

* - `query`
  - `str`
  - The search query string.

* - `types`
  - `List[LavaSearchType]`
  - The types of results to return. At least one must be specified.

* - `search_type`
  - `Optional[SearchType]`
  - The search platform to use (e.g. `ytsearch`, `spsearch`, `scsearch`). Uses the server default if not provided.

* - `ctx`
  - `ContextType | None`
  - Optional Discord context to attach to result tracks.

:::

:::{important}

Raises `NodeRestException` if the LavaSearch plugin is not installed on the node or the request
fails, and `ValueError` if `types` is empty.

:::

## Search types (`LavaSearchType`)

:::{list-table}
:header-rows: 1

* - Value
  - Description

* - `LavaSearchType.TRACK`
  - Returns individual tracks.

* - `LavaSearchType.ALBUM`
  - Returns albums.

* - `LavaSearchType.ARTIST`
  - Returns artists.

* - `LavaSearchType.PLAYLIST`
  - Returns playlists.

* - `LavaSearchType.TEXT`
  - Returns text-based search suggestions.

:::

## The SearchResult object

`load_search()` returns a `SearchResult` object, or `None` if the search yielded no results, with the following attributes:

:::{list-table}
:header-rows: 1

* - Attribute
  - Type
  - Description

* - `tracks`
  - `List[Track]`
  - The tracks found.

* - `albums`
  - `List[Playlist]`
  - The albums found.

* - `artists`
  - `List[Playlist]`
  - The artists found.

* - `playlists`
  - `List[Playlist]`
  - The playlists found.

* - `texts`
  - `List[Text]`
  - Text suggestions returned by the plugin.

* - `plugin_info`
  - `dict`
  - Raw plugin metadata from the response.

:::

## The Text object

Each entry in `SearchResult.texts` is a `Text` object, a text-based search suggestion
returned by the LavaSearch plugin (not a playable track).

:::{list-table}
:header-rows: 1

* - Attribute
  - Type
  - Description

* - `text`
  - `str`
  - The suggested search text.

* - `plugin_info`
  - `dict`
  - Raw plugin metadata for this suggestion.

:::

`str(text_result)` returns the suggestion text directly, so you can print or send it as-is:

```py
for suggestion in result.texts:
    print(suggestion)
```

## Example: search and play the first result

```py
from lava_lyra import LavaSearchType, SearchType


@commands.command(name="search")
async def search(self, ctx, *, query: str):
    if not ctx.voice_client:
        await ctx.invoke(self.join)

    player = ctx.voice_client
    node = player.node

    result = await node.load_search(
        query=query,
        types=[LavaSearchType.TRACK],
        search_type=SearchType.ytsearch,
        ctx=ctx,
    )

    if not result or not result.tracks:
        await ctx.send("No results found.")
        return

    track = result.tracks[0]
    await player.play(track=track)
    await ctx.send(f"Now playing: **{track.title}**")
```

## Example: search Spotify for a track and album

```py
result = await node.load_search(
    query="metallica",
    types=[LavaSearchType.TRACK, LavaSearchType.ALBUM, LavaSearchType.ARTIST],
    search_type=SearchType.spsearch,
    ctx=ctx,
)

if result:
    if result.tracks:
        print("Top track:", result.tracks[0].title)
    if result.albums:
        print("Top album:", result.albums[0].name)
    if result.artists:
        print("Top artist:", result.artists[0].name)
```

:::{note}

Albums, artists, and playlists returned by `load_search()` do not include their full track
lists — only the metadata, and `.uri` is `None` on these entries. There is currently no way
to load the full contents of an album or playlist from a `load_search()` result.

:::
