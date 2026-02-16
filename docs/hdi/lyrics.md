# Use Lyrics

Lyra supports fetching song lyrics via the Lavalink v4 lyrics endpoint and via NodeLink.
Lyrics are managed through the `LyricsManager` class, which is accessible from any player via `Player.lyrics`.

:::{note}

Lyrics support requires either:
- **Lavalink v4** with a lyrics-capable plugin (e.g. [java-lyrics-plugin](https://github.com/topi314/LavaLyrics))
- **NodeLink** (which has lyrics support built-in)

:::

## Fetching lyrics for the current track

To fetch lyrics for the currently playing track, use `Player.lyrics.fetch_lyrics()`:

```py
lyrics = await player.lyrics.fetch_lyrics()

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
  - If `True`, skips the track's original source when searching for lyrics. Default: `False`.

* - `lang`
  - `Optional[str]`
  - Language code for YouTube captions (NodeLink only). Example: `"en"`.

:::

## Fetching lyrics for a specific track

You can also fetch lyrics for any `Track` object, not just the one currently playing:

```py
track = results[0]
lyrics = await player.lyrics.fetch_lyrics(track=track)
```

## Checking if lyrics are available

```py
if player.lyrics.has_lyrics:
    lyrics = player.lyrics.lyrics
    print(f"Provider: {lyrics.provider or lyrics.name}")
    print(f"Lines: {len(lyrics)}")
    print(f"Synced: {lyrics.synced}")
```

## Getting lyrics near the current playback position

Use `Lyrics.get_lyrics_at_time()` to retrieve lines near a specific timestamp:

```py
lyrics = player.lyrics.lyrics
if lyrics:
    current_lines = lyrics.get_lyrics_at_time(
        time_seconds=player.position / 1000.0,
        range_seconds=3.0
    )
    for line in current_lines:
        print(line.text)
```

Or use the convenience method on the manager directly:

```py
current_lines = player.lyrics.get_current_lyrics_lines(range_seconds=3.0)
for line in current_lines:
    print(line.text)
```

## Live lyrics (Lavalink v4 only)

Lavalink v4 supports subscribing to live lyric updates. When subscribed, the
`on_lyra_lyrics_update` event fires whenever the current lyric line changes.

### Subscribing to live lyrics

```py
success = await player.lyrics.subscribe_lyrics()
if success:
    print("Subscribed to live lyrics!")
```

```py
@commands.Cog.listener()
async def on_lyra_lyrics_update(self, player, track, line):
    print(f"[{line.time:.1f}s] {line.text}")
```

### Unsubscribing from live lyrics

```py
await player.lyrics.unsubscribe_lyrics()
```

:::{note}

NodeLink does not support the live lyrics subscription endpoint. Use `fetch_lyrics()` for one-time retrieval instead.

:::

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
  - The provider of the lyrics (Lavalink format).

* - `text`
  - `Optional[str]`
  - The full lyrics as a plain string (if available).

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
  - The language code of the lyrics (NodeLink format).

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

* - `on_lyra_lyrics_unavailable`
  - `player, track`
  - Fired when no lyrics are available for the track.

* - `on_lyra_lyrics_update`
  - `player, track, line`
  - Fired when the current lyric line changes (live subscription).

:::

```py
@commands.Cog.listener()
async def on_lyra_lyrics_found(self, player, track, lyrics):
    print(f"Lyrics found for {track.title}: {len(lyrics)} lines")

@commands.Cog.listener()
async def on_lyra_lyrics_unavailable(self, player, track):
    print(f"No lyrics available for {track.title}")
```
