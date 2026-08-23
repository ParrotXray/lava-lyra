# Use the Player class

The `Player` class is the class you will be interacting with the most within Lyra.

It has a number of functions you will be using frequently:

- `Player.add_filter()`
- `Player.build_track()`
- `Player.destroy()`
- `Player.edit_filter()`
- `Player.get_recommendations()`
- `Player.get_tracks()`
- `Player.move_to()`
- `Player.play()`
- `Player.remove_filter()`
- `Player.reset_filters()`
- `Player.seek()`
- `Player.set_pause()`
- `Player.set_volume()`
- `Player.stop()`
- `Player.fetch_lyrics()`
- `Player.subscribe_lyrics()`
- `Player.unsubscribe_lyrics()`
- `Player.get_current_lyrics_lines()`


There are also properties the `Player` class has to access certain values:


:::{list-table}
:header-rows: 1

* - Property
  - Type
  - Description

* - `Player.bot`
  - `BotType`
  - Returns the bot associated with this player instance (a Discord.py or Py-cord `Client`/`commands.Bot`).

* - `Player.channel`
  - `Optional[Union[VoiceChannel, StageChannel]]`
  - Returns the voice or stage channel this player is connected to, or `None` after `disconnect()`.

* - `Player.client`
  - `BotType`
  - Same object as `Player.bot`. Required by discord.py's `VoiceProtocol` contract, which sets/reads this attribute directly.

* - `Player.current`
  - `Optional[Track]`
  - Returns the currently playing track, or `None` if nothing is loaded.

* - `Player.filters`
  - `Filters`
  - Returns the helper class for interacting with filters.

* - `Player.guild`
  - `Guild`
  - Returns the guild associated with the player.

* - `Player.is_connected`
  - `bool`
  - Returns whether or not the player is connected.

* - `Player.is_dead`
  - `bool`
  - Returns whether the player is dead or not. A player is considered dead if it has been destroyed and removed from stored players.

* - `Player.is_paused`
  - `bool`
  - Returns whether or not the player is connected and paused. This only checks the connection and paused state, not whether a track is currently loaded — see `Player.current` for that.

* - `Player.is_playing`
  - `bool`
  - Returns whether or not the player has a track loaded and connected. This stays `True` while paused — check `Player.is_paused` separately.

* - `Player.node`
  - `Node`
  - Returns the node the player is connected to.

* - `Player.position`
  - `int`
  - Returns the player’s position in a track in milliseconds.

* - `Player.adjusted_position`
  - `float`
  - Returns the player’s position in a track in milliseconds, adjusted for rate if affected.

* - `Player.adjusted_length`
  - `float`
  - Returns the current track length in milliseconds, adjusted for rate if affected.

* - `Player.rate`
  - `float`
  - Returns the players current rate, which represents the speed of the currently playing track. This rate is affected by the `Timescale` filter.

* - `Player.volume`
  - `int`
  - Returns the players current volume.

* - `Player.lyrics_loaded`
  - `bool`
  - Returns whether lyrics have been attempted to load for the current track.

* - `Player.lyrics`
  - `Lyrics | None`
  - Returns the currently loaded `Lyrics` object for the current track, or `None` if none have been loaded.

* - `Player.has_lyrics`
  - `bool`
  - Returns whether lyrics currently exist for the current track.

* - `Player.is_subscribed`
  - `bool`
  - Returns whether the player is subscribed to live lyrics.

:::

To fetch lyrics for a track on demand, use `Player.fetch_lyrics()`

```py
lyrics = await Player.fetch_lyrics(track=<optional Track, defaults to the current track>, skip_track_source=False, lang=None)
```

For continuously updating (live) lyrics, use `Player.subscribe_lyrics()` / `Player.unsubscribe_lyrics()`,
and `Player.get_current_lyrics_lines()` to fetch the lines around the current position:

```py
await Player.subscribe_lyrics(skip_track_source=False)
lines = Player.get_current_lyrics_lines(range_seconds=5.0)
await Player.unsubscribe_lyrics()
```

See [](lyrics.md) for the full lyrics API.

## Getting tracks

To get tracks using Lavalink, we need to use `Player.get_tracks()`

You can also use `Node.get_tracks()` to do the same thing but without having a player.

```py
await Player.get_tracks(...)
```

After you have initialized your function, we need to fill in the proper parameters:

:::{list-table}
:header-rows: 1

* - Name
  - Type
  - Description

* - `query`
  - `str`
  - The string you want to search up

* - `ctx`
  - `ContextType | None`
  - Optional value which sets a `Context` object on the tracks you search.

* - `search_type`
  - `SearchType | None`
  - Enum which sets the provider to search from. Default value is `SearchType.ytsearch`

* - `filters`
  - `Optional[List[Filter]]`
  - Optional value which sets the filters that should apply when the track is played on the tracks you search.

:::

After you set those parameters, your function should look something like this:

```py

await Player.get_tracks(
    query="<your query here>",
    ctx=<optional ctx object here>,
    search_type=<optional search type here>,
    filters=[<optional filters here>]
)

```

:::{note}

Platform support (Spotify, Apple Music, etc.) is resolved by your Lavalink server's plugins.
No credentials are needed on the client side — configure them in your `application.yml` instead.

:::



This returns `list[Track] | Playlist | None` depending on what was loaded — check the type before using the result.
Raises `TrackLoadError` if the query can't be resolved.
Ideally, you should be putting all tracks into some sort of a queue. If you would like to learn about how to use
our queue implementation, you can refer to [](queue.md)


## Getting recommendations

To get recommendations using Lavalink, we need to use `Player.get_recommendations()`

You can also use `Node.get_recommendations()` to do the same thing without having a player.

```py
await Player.get_recommendations(...)
```

After you have initialized your function, we need to fill in the proper parameters:

:::{list-table}
:header-rows: 1

* - Name
  - Type
  - Description

* - `track`
  - `Track`
  - The track to fetch recommendations for

* - `ctx`
  - `ContextType | None`
  - Optional value which sets a `Context` object on the recommendations you fetch.

:::

After you set those parameters, your function should look something like this:

```py

await Player.get_recommendations(
    track=<your track object here>,
    ctx=<optional ctx object here>,
)

```

This returns `list[Track] | Playlist | None` depending on what was loaded — check the type before using the result.
Raises `TrackLoadError` if the track's source isn't supported for recommendations, and `NodeRestException`
if the required plugin isn't installed on the node or the request otherwise fails.
Ideally, you should be putting all tracks into some sort of a queue. If you would like to learn about how to use
our queue implementation, you can refer to [](queue.md)

## Building a track from an identifier

If you already have a valid Lavalink track identifier (for example, one saved from a previous
session) and want to turn it back into a `Track` object without running a new search, use
`Player.build_track()`

```py
await Player.build_track(...)
```

After you have initialized your function, we need to fill in the proper parameters:

:::{list-table}
:header-rows: 1

* - Name
  - Type
  - Description

* - `identifier`
  - `str`
  - The Lavalink track identifier to build a track from

* - `ctx`
  - `ContextType | None`
  - Optional value which sets a `Context` object on the track it builds.

:::

After you set those parameters, your function should look something like this:

```py

await Player.build_track(
    identifier="<your track identifier here>",
    ctx=<optional ctx object here>,
)

```

After running this function, you should get a `Track` object back, ready to be played or queued.

## Connecting a player

To connect a player to a channel you need to pass the `Player` class into your `channel.connect()` function:

```py
await voice_channel.connect(cls=Player)
```

This will instance the player and make it available to your guild. If you want to access your player after instancing it,
you must use either `Guild.voice_client` or `Context.voice_client`.

Discord's `connect()` only forwards the `cls` argument, so `Player` picks a node for you via
`NodePool.get_node()`. If you need a specific node instead, instantiate `Player` yourself and pass
`node=<your Node here>`, then hand that instance to `channel.connect(cls=lambda *a, **kw: player)`.

## Controlling the player

There are a few functions to control the player:

- `Player.destroy()`
- `Player.disconnect()`
- `Player.play()`
- `Player.seek()`
- `Player.set_pause()`
- `Player.set_volume()`
- `Player.stop()`

### Disconnecting a player

To disconnect a player from its voice channel without destroying it on the node, we need to use `Player.disconnect()`

```py
await Player.disconnect()
```

`Player.disconnect()` also accepts an optional `force` parameter, which is a boolean.

:::{note}

`force` is currently accepted but not read anywhere internally — passing `force=True` has no effect on current behavior.

:::

```py

await Player.disconnect(force=<True/False>)

```

:::{note}

This leaves the voice channel and runs cleanup, but keeps the player entry alive on the Lavalink/NodeLink node. If you also want the node-side player removed, use `Player.destroy()` instead — it calls `disconnect()` for you as part of its own cleanup.

:::

### Destroying a player

To destroy a player, we need to use `Player.destroy()`

```py
await Player.destroy()
```

### Playing a track

To play a track, we need to use `Player.play()`

```py
await Player.play(...)
```

After you have initialized your function, we need to fill in the proper parameters:

:::{list-table}
:header-rows: 1

* - Name
  - Type
  - Description

* - `track`
  - `Track`
  - The track to play

* - `start`
  - `int`
  - The time (in milliseconds) to start the track at. Default value is `0`

* - `end`
  - `int`
  - The time (in milliseconds) to end the track at. Default value is `0`

* - `ignore_if_playing`
  - `bool`
  - If set to `True`, sends `noReplace=true` to Lavalink so the currently playing track is **not** replaced. Default value is `False` (the current track is replaced).

* - `gapless`
  - `bool`
  - **NodeLink-only.** If set to `True`, queues the track as the next track for a gapless transition instead of replacing the currently playing one. Raises `NodelinkExclusive` if the node is a plain Lavalink node. Default value is `False`.

:::

After you set those parameters, your function should look something like this:

```py

await Player.play(
    track=<your track object here>,
    start=<your optional start time here>,
    end=<your optional end time here>,
    ignore_if_playing=<your optional boolean here>,
    gapless=<your optional boolean here>
)

```

After running this function, it should return the `Track` you specified when running the function.

:::{note}

The track isn't necessarily playing immediately after this returns: with `gapless=True` it's queued as the *next* track rather than started right away, and if the node isn't currently available `play()` waits a second and returns the track without ever sending the play request.

:::

Raises `TrackLoadError` if the track can't be resolved (e.g. it has no ISRC and no title/author match is
found), `NodelinkExclusive` if `gapless=True` on a plain Lavalink node, and re-raises
`NodeNotAvailable`/`NodeRestException` for any node error that isn't a recoverable session issue.


### Seeking to a position

To seek to a position, we need to use `Player.seek()`

```py
await Player.seek(...)
```

After you have initialized your function, we need to include the `position` parameter, which is an amount in milliseconds:

```py

await Player.seek(position=<your pos here>)

```

After running this function, your currently playing track should seek to your specified position

:::{important}

Raises `TrackInvalidPosition` if `position` is negative or greater than the current track's length.

:::


### Pausing/unpausing the player


To pause/unpause the player, we need to use `Player.set_pause()`

```py
await Player.set_pause(...)
```

After you have initialized your function, we need to include the `pause` parameter, which is a boolean:

```py

await Player.set_pause(pause=<True/False>)

```
After running this function, your currently playing track should either pause or unpause depending on what you set.

### Setting the player volume

To set the volume the player, we need to use `Player.set_volume()`

```py
await Player.set_volume(...)
```

:::{important}
Lavalink accepts ranges from 0 to 1000 for this parameter. Inputting a value either higher or lower
than this amount will **not work.**
:::

After you have initialized your function, we need to include the `volume` parameter, which is an integer:

```py

await Player.set_volume(volume=<int>)

```
After running this function, your currently playing track should adjust in volume depending on the volume you set.

### Stopping the player

To stop the player, we need to use `Player.stop()`

```py
await Player.stop()
```

`Player.stop()` also accepts an optional `gapless` keyword argument (**NodeLink-only**,
`False` by default). When set to `True`, it clears the queued next-track instead of the
currently playing one, and raises `NodelinkExclusive` on a plain Lavalink node:

```py
await Player.stop(gapless=True)
```

### Moving the player to another channel

To move the player to another channel, we need to use `Player.move_to()`

```py
await Player.move_to(...)
```

After you have initialized your function, we need to include the `channel` parameter, which is a `VoiceChannel` or `StageChannel`:

```py
await Player.move_to(channel)
```

After running this function, your player should be in the new voice channel. All voice state updates should also be handled.


## Controlling filters

Lyra has an extensive suite of filter management tools to help you make the most of Lavalink and it's filters.

Here are some of the functions you will be using to control filters:

- `Player.add_filter()`
- `Player.edit_filter()`
- `Player.remove_filter()`
- `Player.reset_filters()`


### Adding a filter


To add a filter, we need to use `Player.add_filter()`

```py
await Player.add_filter(...)
```


After you have initialized your function, we need to fill in the proper parameters:

:::{list-table}
:header-rows: 1

* - Name
  - Type
  - Description

* - `_filter`
  - `Filter`
  - The filter to apply

* - `fast_apply`
  - `bool`
  - If set to `True`, the specified filter will apply (almost) instantly if a song is playing. Default value is `False`.

:::

After you set those parameters, your function should look something like this:

```py

await Player.add_filter(
    _filter=<your filter object here>,
    fast_apply=<True/False>
)

```

After running this function, you should see your currently playing track sound different depending on the filter you chose.

Raises `FilterTagAlreadyInUse` if a filter with the same `tag` is already applied, or
`NodelinkExclusive` if the filter is Nodelink-exclusive and the node isn't a Nodelink instance.

### Removing a filter


To remove a filter, we need to use `Player.remove_filter()`

```py
await Player.remove_filter(...)
```


After you have initialized your function, we need to fill in the proper parameters:

:::{list-table}
:header-rows: 1

* - Name
  - Type
  - Description

* - `filter_tag`
  - `str`
  - The tag of the filter to remove

* - `fast_apply`
  - `bool`
  - If set to `True`, the specified filter will be removed (almost) instantly if a song is playing. Default value is `False`.

:::

After you set those parameters, your function should look something like this:

```py

await Player.remove_filter(
    filter_tag=<your filter tag here>,
    fast_apply=<True/False>
)

```

After running this function, you should see your currently playing track sound different depending on the filter you chose to remove.

Raises `FilterTagInvalid` if no filter with that `filter_tag` is currently applied.

### Editing a filter

To edit a filter that's already applied without removing and re-adding it, we need to use
`Player.edit_filter()`

```py
await Player.edit_filter(...)
```

After you have initialized your function, we need to fill in the proper parameters:

:::{list-table}
:header-rows: 1

* - Name
  - Type
  - Description

* - `filter_tag`
  - `str`
  - The tag of the filter you want to replace

* - `edited_filter`
  - `Filter`
  - The new filter to replace it with. It must share the same tag as the filter being replaced.

* - `fast_apply`
  - `bool`
  - If set to `True`, the edited filter will apply (almost) instantly if a song is playing. Default value is `False`.

:::

After you set those parameters, your function should look something like this:

```py

await Player.edit_filter(
    filter_tag=<your filter tag here>,
    edited_filter=<your new filter object here>,
    fast_apply=<True/False>
)

```

After running this function, you should see your currently playing track sound different depending on the edit you made.

:::{important}

Raises `NodelinkExclusive` if the filter is Nodelink-exclusive and the node isn't a Nodelink instance, `FilterTagInvalid` if no filter with `filter_tag` exists, and `FilterInvalidArgument` if `edited_filter` isn't the same type as the current filter, is identical to it, or has a different tag.

:::

### Resetting all filters

To reset all filters, we need to use `Player.reset_filters()`. Note that this removes every filter entirely, rather than resetting each one to its own default parameters — for that, use `Filter.reset()` on an individual filter instead.

```py
await Player.reset_filters()
```

Raises `FilterInvalidArgument` if no filters are currently applied.

After you have initialized your function, you can optionally include the `fast_apply` parameter, which is a boolean. If this is set to `True`, it'll remove all filters (almost) instantly if theres a track playing.

```py

await Player.reset_filters(fast_apply=<True/False>)

```
