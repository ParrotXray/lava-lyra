# Use the Filter class

Lyra takes full advantage of the Lavalink filter system by using a unique system to apply filters on top of one another. We call this system "filter stacking". With this system, we can stack filters of different types on top of one another to produce one-of-a-kind audio effects on playback while still being able to easily manage each filter. Only one filter of a given type may be active at once — adding a second filter of the same type raises `FilterTagAlreadyInUse`.


## Types of filters

Lavalink, and by extension, Lyra, has different types of filters you can use.

Here are the different types and what they do:

:::{list-table}
:header-rows: 1

* - Type
  - Class
  - Description

* - Channel Mix
  - `lava_lyra.ChannelMix()`
  - Adjusts stereo panning of a track.

* - Distortion
  - `lava_lyra.Distortion()`
  - Generates a distortion effect on a track.

* - Equalizer
  - `lava_lyra.Equalizer()`
  - Represents a 15 band equalizer. You can adjust the dynamic of the sound using this filter.

* - Karaoke
  - `lava_lyra.Karaoke()`
  - Filters the vocals from the track.

* - Low Pass
  - `lava_lyra.LowPass()`
  - Filters out high frequencies and only lets low frequencies pass through.

* - Rotation
  - `lava_lyra.Rotation()`
  -  Produces a stereo-like panning effect, which sounds like the audio is being rotated around the listener’s head

* - Timescale
  - `lava_lyra.Timescale()`
  - Adjusts the speed and pitch of a track.

* - Tremolo
  - `lava_lyra.Tremolo()`
  - Rapidly changes the volume of the track, producing a wavering tone.

* - Vibrato
  - `lava_lyra.Vibrato()`
  - Rapidly changes the pitch of the track.

:::

### NodeLink-exclusive filters

The following filters are not part of the standard Lavalink filter set. They require a NodeLink
instance and will raise `NodelinkExclusive` if applied against a plain Lavalink node:

:::{list-table}
:header-rows: 1

* - Type
  - Class
  - Description

* - Chorus
  - `lava_lyra.Chorus()`
  - Simulates multiple voices playing at once by mixing the signal with modulated, delayed copies of itself.

* - Compressor
  - `lava_lyra.Compressor()`
  - Applies dynamic range compression, balancing out the loud and quiet parts of the audio.

* - Echo
  - `lava_lyra.Echo()`
  - Creates delay-based repetitions of the audio with feedback control, producing an echo effect.

* - Highpass
  - `lava_lyra.Highpass()`
  - Attenuates low frequencies, letting higher frequencies pass through. Unlike `LowPass`, this uses a different payload key and is NodeLink-only.

* - Phaser
  - `lava_lyra.Phaser()`
  - Sweeps a series of all-pass filters across the frequency spectrum, producing a swirling effect.

* - Spatial
  - `lava_lyra.Spatial()`
  - Creates a spatial audio effect using modulated cross-channel delays.

:::

Each filter has individual values you can adjust to fine-tune the sound of the filter. If you want to see what values each filter has, refer to the parameter table below.

If you are stuck on what values adjust what, some filters include presets that you can apply to get a certain sound. You can also play around with the values and generate your own unique sound if you'd like.

### Presets

- `Equalizer.flat()` — All 15 bands reset to `0.0`, i.e. a neutral/flat EQ.
- `Equalizer.boost()` — Boosts bass and highs for a fun, energetic sound.
- `Equalizer.metal()` — Boosts the mids for a fuller, concert-like sound, geared toward metal.
- `Equalizer.piano()` — Boosts mids/highs and cuts some lows/highs, geared toward piano-heavy tracks.
- `Timescale.vaporwave()` — Slows the track down (`speed=0.8, pitch=0.8`) for a half-speed, vaporwave effect. Tag is `"vaporwave"`.
- `Timescale.nightcore()` — Speeds the track up (`speed=1.25, pitch=1.3`) for a nightcore effect. Tag is `"nightcore"`.

Each preset is a classmethod that returns a ready-to-use filter instance, e.g. `lava_lyra.Timescale.nightcore()`.

### Parameter reference

:::{important}

Every filter also takes a keyword-only `tag: str`, required, not listed below since it's shared
by all filters.

:::

:::{note}

Every filter also takes an optional keyword-only `transition: dict`, not listed below since it's
shared by all filters. Use it to smoothly animate the filter's parameters instead of applying
them instantly. Only honored by NodeLink v3.7.0+, ignored on plain Lavalink or older NodeLink.
Accepted keys: `durationMs` (int, must be greater than `0`) and `curve` (str, one of `linear`,
`exponential`, `sinusoidal`). NodeLink falls back to `sinusoidal` server-side if `curve` is
omitted or not one of these. `transition` is ignored entirely if `durationMs` is missing or
`<= 0` — the filter is applied instantly in that case, same as when `transition` isn't passed
at all.
:::

:::{list-table}
:header-rows: 1

* - Filter
  - Parameters (default)
  - Validation

* - `ChannelMix`
  - `left_to_left=1`, `right_to_right=1`, `left_to_right=0`, `right_to_left=0`
  - Each value must be between `0` and `1` (inclusive).

* - `Distortion`
  - `sin_offset=0`, `sin_scale=1`, `cos_offset=0`, `cos_scale=1`, `tan_offset=0`, `tan_scale=1`, `offset=0`, `scale=1`
  - No validation; any `float` is accepted.

* - `Equalizer`
  - `levels: list[tuple[int, float]]` (required, no default)
  - Each band index must be between `0` and `14` (inclusive).

* - `Karaoke`
  - `level=1.0`, `mono_level=1.0`, `filter_band=220.0`, `filter_width=100.0`
  - No validation; any `float` is accepted.

* - `LowPass`
  - `smoothing=20`
  - No validation. Sent under both `lowPass` (Lavalink) and `lowpass` (NodeLink < 3.7.0) keys.

* - `Rotation`
  - `rotation_hertz=5`
  - No validation; any `float` is accepted.

* - `Timescale`
  - `speed=1.0`, `pitch=1.0`, `rate=1.0`
  - Each value must be greater than `0`.

* - `Tremolo`
  - `frequency=2.0`, `depth=0.5`
  - `frequency` must be greater than `0` (no upper cap). `depth` must be between `0` and `1`.

* - `Vibrato`
  - `frequency=2.0`, `depth=0.5`
  - `frequency` must be greater than `0` and at most `14`. `depth` must be between `0` and `1`.

:::

The following NodeLink-exclusive filters have their own parameters and validation:

:::{list-table}
:header-rows: 1

* - Filter
  - Parameters (default)
  - Validation

* - `Chorus`
  - `rate=1.5`, `depth=0.5`, `delay=25`, `mix=0.6`, `feedback=0.2`
  - `depth` and `mix` between `0`-`1`; `delay` between `1`-`45` (ms); `feedback` between `0`-`0.95`.

* - `Compressor`
  - `threshold=-20`, `ratio=4`, `attack=10`, `release=100`, `gain=5`
  - `ratio` must be `1.0` or greater; `attack` and `release` must be `0` or greater (ms).

* - `Echo`
  - `delay=500`, `feedback=0.3`, `mix=0.5`
  - `delay` between `0`-`5000` (ms) on Lavalink; NodeLink clamps `delay` to `2000` ms. `feedback` and `mix` between `0`-`1`.

* - `Highpass`
  - `smoothing=20`
  - `smoothing` must be greater than `1.0`. Payload key is `highpass` (lowercase, unlike `LowPass`'s `lowPass`).

* - `Phaser`
  - `stages=6`, `rate=0.5`, `depth=0.7`, `feedback=0.5`, `mix=0.5`, `min_frequency=200`, `max_frequency=2000`
  - `stages` between `2`-`12`; `depth`/`mix` between `0`-`1`; `feedback` between `0`-`0.9`; frequencies must be positive and `min_frequency < max_frequency`.

* - `Spatial`
  - `depth=0.8`, `rate=0.3`
  - `depth` must be between `0` and `1`. `rate` is unvalidated.

:::

## Editing a filter

Instead of removing and re-adding a filter to change its values, you can edit it in place with
`Filter.update()`, which only overwrites the parameters you pass in:

```py
my_filter = lava_lyra.LowPass(tag="lowpass", smoothing=15.0)
await player.add_filter(_filter=my_filter)

# Later, build the updated filter and swap it in with the same tag:
updated_filter = lava_lyra.LowPass(tag="lowpass", smoothing=15.0).update(smoothing=25.0)
await player.edit_filter(filter_tag="lowpass", edited_filter=updated_filter, fast_apply=True)
```

Passing an unknown parameter name raises `FilterInvalidArgument`.

To reset a filter back to its default parameter values (while keeping its `tag`), use `Filter.reset()`:

```py
my_filter.reset()
```

:::{warning}

`Equalizer.reset()` is a no-op. `Equalizer`'s only parameter, `levels`, has no default value
(it's required), so there's nothing for `Filter.reset()` to fall back to — it leaves the current
`levels` untouched. To reset an EQ, replace it instead: `Equalizer.flat()` gives you a neutral
15-band EQ you can pass to `Player.edit_filter()`.

:::

Both `update()` and `reset()` mutate the filter in place and return `self`, so you can chain them.

## Adding a filter

:::{important}

You must have the `Player` class initialized first before using this. Refer to [](player.md)

:::

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

:::{important}

Raises `FilterTagAlreadyInUse` if a filter with the same `tag` is already applied. Raises
`NodelinkExclusive` if `_filter` is a Nodelink-exclusive filter and `node` isn't a Nodelink
instance.

:::

## Removing a filter

:::{important}

You must have the `Player` class initialized first before using this. Refer to [](player.md)

:::


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

:::{important}

Raises `FilterTagInvalid` if no filter with that `filter_tag` is currently applied.

:::


## Resetting all filters

:::{important}

You must have the `Player` class initialized first before using this. Refer to [](player.md)

:::

To reset all filters, we need to use `Player.reset_filters()`

```py
await Player.reset_filters()
```

:::{important}

Raises `FilterInvalidArgument` if no filters are currently applied — you must have at least one
filter on the player first.

:::


After you have initialized your function, you can optionally include the `fast_apply` parameter, which is a boolean. If this is set to `True`, it'll remove all filters (almost) instantly if theres a track playing.

```py

await Player.reset_filters(fast_apply=<True/False>)

```

## Inspecting the current filters

:::{important}

You must have the `Player` class initialized first before using this. Refer to [](player.md)

:::

Unlike adding/removing/editing filters, checking what's currently applied doesn't need to talk to
the node, so these are plain (non-`async`) methods and properties on `Player.filters` rather than
on `Player` directly. It has a few things you'll use:

:::{list-table}
:header-rows: 1

* - Member
  - Description

* - `Player.filters.get_filters()`
  - Returns the current list of applied filters, as `List[Filter]`.

* - `Player.filters.has_filter(filter_tag=...)`
  - `bool` method. Whether a filter with the given tag is currently applied.

* - `Player.filters.has_filter_type(filter_type=...)`
  - `bool` method. Whether any applied filter matches the type of the `Filter` instance you pass in.

* - `Player.filters.get_preload_filters()`
  - Returns every applied filter that was preloaded via `get_tracks(filters=...)`, as `List[Filter]`.

* - `Player.filters.get_all_payloads()`
  - Returns a merged `Dict[str, Any]` of every applied filter's Lavalink/NodeLink payload, ready to send as-is.

* - `Player.filters.has_preload`
  - `bool` property. Whether any applied filter was preloaded.

* - `Player.filters.has_global`
  - `bool` property. Whether any applied filter is global (i.e. not preloaded).

* - `Player.filters.empty`
  - `bool` property. Whether there are no filters applied at all.

:::

:::{important}

When you call `Player.play()`, global (non-preloaded) filters take precedence over the
track's own per-track filters (`track.filters`, set via `get_tracks(filters=...)`). If any
global filter is applied, per-track filters are skipped entirely for that `play()` call —
they only get applied when no global filters are currently active.

:::

For example, to check whether a `LowPass` filter is currently applied before adding another one:

```py
if not player.filters.has_filter_type(filter_type=lava_lyra.LowPass(tag="lowpass")):
    await player.add_filter(_filter=lava_lyra.LowPass(tag="lowpass", smoothing=15.0))
```
