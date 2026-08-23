# Use Lyrics

Lyra supports fetching song lyrics via the Lavalink v4 lyrics endpoint and via NodeLink.
Lyrics are accessed through methods on the `Player` class (such as `Player.fetch_lyrics()` and `Player.subscribe_lyrics()`), with the cached `Lyrics` object exposed via the `Player.lyrics` property.

:::{note}

Lyrics support requires either:
- **Lavalink v4** with a lyrics-capable plugin (e.g. [topi314/LavaLyrics](https://github.com/topi314/LavaLyrics))
- **NodeLink** (which has lyrics support built-in)

:::

:::{important}

You must also pass `lyrics=True` to `NodePool.create_node()` when adding the node. It defaults
to `False`, and every method on this page will silently no-op without raising an error if lyrics
support isn't enabled on the node: `fetch_lyrics()` returns `None`, `subscribe_lyrics()` and
`unsubscribe_lyrics()` return `False`, and `get_current_lyrics_lines()` returns `[]`. You can
check this at any time with `Node.lyrics_enabled`.

`fetch_lyrics()` also returns `None` on any other failure (network errors, bad response, etc.) —
it catches everything internally and just logs it. A `None` result isn't only "lyrics disabled".

:::

## Fetching lyrics for the current track

To fetch lyrics for the currently playing track, use `Player.fetch_lyrics()`:

```py
lyrics = await player.fetch_lyrics()

if lyrics:
    for line in lyrics:
        print(f"[{line.time:.1f}s] {line.text}")
else:
    print("No lyrics found.")
```

### Fetch parameters

:::{list-table}
:header-rows: 1

* - Name
  - Type
  - Description

* - `track`
  - `Optional[Track]`
  - The track to fetch lyrics for. Defaults to the currently playing track.

* - `skip_track_source`
  - `bool`
  - If `True`, skips the track's original source when searching for lyrics (Lavalink v4 only). Default: `False`.

* - `lang`
  - `Optional[str]`
  - Language code for YouTube captions (NodeLink only). Example: `"en"`.

:::

## Fetching lyrics for a specific track

You can also fetch lyrics for any `Track` object, not just the one currently playing:

```py
track = results[0]
lyrics = await player.fetch_lyrics(track=track)
```

## Checking if lyrics are available

```py
if player.has_lyrics:
    lyrics = player.lyrics
    print(f"Provider: {lyrics.provider or lyrics.name}")
    print(f"Lines: {len(lyrics)}")
    print(f"Synced: {lyrics.synced}")
```

## Getting lyrics near the current playback position

Use `Lyrics.get_lyrics_at_time()` to retrieve lines near a specific timestamp:

```py
lyrics = player.lyrics
if lyrics:
    current_lines = lyrics.get_lyrics_at_time(
        time_seconds=player.position / 1000.0, range_seconds=3.0
    )
    for line in current_lines:
        print(line.text)
```

Or use the convenience method on the player directly:

```py
current_lines = player.get_current_lyrics_lines(range_seconds=3.0)
for line in current_lines:
    print(line.text)
```

## Live lyrics

Lavalink v4 (with the LavaLyrics plugin) and NodeLink both support subscribing
to live lyric updates. When subscribed, the `on_lyra_lyrics_line` event fires
whenever the current lyric line changes.

### Subscribing to live lyrics

```py
success = await player.subscribe_lyrics()
if success:
    print("Subscribed to live lyrics!")
```

`subscribe_lyrics()` also accepts `skip_track_source`, sent as a query parameter regardless of node type (unlike `fetch_lyrics()`, it isn't gated to Lavalink v4).

```py
from discord.ext import commands


@commands.Cog.listener()
async def on_lyra_lyrics_line(self, player, track, line):
    print(f"[{line.time:.1f}s] {line.text}")
```

### Unsubscribing from live lyrics

```py
await player.unsubscribe_lyrics()
```

### Checking subscription status

```py
if player.is_subscribed:
    print("Currently subscribed to live lyrics")
```

## The Lyrics object

The `Lyrics` object has the following properties:

:::{list-table}
:header-rows: 1

* - Property
  - Type
  - Description

* - `source_name`
  - `Optional[str]`
  - The name of the lyrics source (Lavalink format).

* - `provider`
  - `Optional[str]`
  - The provider of the lyrics. Set by both the Lavalink and NodeLink parsing paths.

* - `text`
  - `Optional[str]`
  - The full lyrics as a plain string. Set on the Lavalink v4 path and on NodeLink's live-lyrics
    websocket events; the NodeLink REST fetch doesn't include it, so it's `None` there.

* - `lines`
  - `List[LyricLine]`
  - List of timestamped lyric lines.

* - `synced`
  - `bool`
  - Whether the lyrics are time-synced (NodeLink format).

* - `name`
  - `Optional[str]`
  - The name/title of the lyrics entry (NodeLink format).

* - `lang`
  - `Optional[str]`
  - The language code of the lyrics. NodeLink doesn't return this field in its lyrics data —
    always `None` there; only usable as a request parameter, not a response field.

:::

Each `LyricLine` has:

:::{list-table}
:header-rows: 1

* - Property
  - Type
  - Description

* - `text`
  - `str`
  - The text of this lyric line.

* - `time`
  - `float`
  - The timestamp in seconds when this line should be displayed.

* - `duration`
  - `Optional[float]`
  - The duration in seconds this line is displayed (if available).

:::

## Listening for lyrics events

:::{list-table}
:header-rows: 1

* - Event
  - Arguments
  - Description

* - `on_lyra_lyrics_found`
  - `player, track, lyrics`
  - Fired when lyrics are successfully found.

* - `on_lyra_lyrics_not_found`
  - `player, track`
  - Fired when no lyrics are available for the track.

* - `on_lyra_lyrics_line`
  - `player, track, line`
  - Fired when the current lyric line changes (live subscription).

:::

```py
from discord.ext import commands


@commands.Cog.listener()
async def on_lyra_lyrics_found(self, player, track, lyrics):
    print(f"Lyrics found for {track.title}: {len(lyrics)} lines")


@commands.Cog.listener()
async def on_lyra_lyrics_not_found(self, player, track):
    print(f"No lyrics available for {track.title}")
```
