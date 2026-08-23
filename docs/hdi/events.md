# Use the Events class

Lyra has different events that are triggered depending on events emitted by Lavalink or the library itself.

Here is the full list of events:

- `TrackStartEvent` → `on_lyra_track_start`
- `TrackEndEvent` → `on_lyra_track_end`
- `TrackStuckEvent` → `on_lyra_track_stuck`
- `TrackExceptionEvent` → `on_lyra_track_exception`
- `WebSocketClosedEvent` → `on_lyra_websocket_closed`
- `LyricsFoundEvent` → `on_lyra_lyrics_found`
- `LyricsNotFoundEvent` → `on_lyra_lyrics_not_found`
- `LyricsLineEvent` → `on_lyra_lyrics_line`
- `NodeConnectedEvent` → `on_lyra_node_connected`
- `NodeDisconnectedEvent` → `on_lyra_node_disconnected`
- `NodeReconnectingEvent` → `on_lyra_node_reconnecting`
- `PlayerCreatedEvent` → `on_lyra_player_created`
- `VolumeChangedEvent` → `on_lyra_volume_changed`
- `PlayerConnectedEvent` → `on_lyra_player_connected`
- `FiltersChangedEvent` → `on_lyra_filters_changed`
- `PauseEvent` → `on_lyra_pause`
- `SeekEvent` → `on_lyra_seek`
- `MixStartedEvent` → `on_lyra_mix_started`
- `MixEndedEvent` → `on_lyra_mix_ended`

Here is an example of how you would listen for the `TrackStartEvent` within a cog:

```py
import lava_lyra
from discord.ext import commands


@commands.Cog.listener()
async def on_lyra_track_start(self, player: lava_lyra.Player, track: lava_lyra.Track):
    print(f"Now playing: {track.title}")
```

## Event definitions

### Track events

All track-related events carry a `Player` object and a `Track` object.

- `on_lyra_track_start(player, track)` — Fired when a track starts playing.
- `on_lyra_track_end(player, track, reason)` — Fired when a track ends. `reason` is a string describing why the track ended.
- `on_lyra_track_stuck(player, track, threshold)` — Fired when a track gets stuck. `threshold` is the time in milliseconds Lavalink waited before giving up.
- `on_lyra_track_exception(player, track, exception)` — Fired when a track fails to play. `exception` is a `TrackExceptionPayload` object with `message`, `severity`, and `cause` attributes.

### Websocket events

- `on_lyra_websocket_closed(payload)` — Fired when the Discord voice websocket for a guild is closed, relayed by the node (not the node's own websocket connection). `payload` is a `WebSocketClosedPayload` object with `guild`, `code`, `reason`, and `by_remote` attributes.

### Lyrics events

- `on_lyra_lyrics_found(player, track, lyrics)` — Fired when lyrics are found for the current track. `lyrics` is a `Lyrics` object.
- `on_lyra_lyrics_not_found(player, track)` — Fired when lyrics are not available for the current track.
- `on_lyra_lyrics_line(player, track, line)` — Fired when the current lyric line changes (live lyrics subscription). `line` is a `LyricLine` object.

### Node events

- `on_lyra_node_connected(node_id, is_nodelink, reconnect)` — Fired when a node connects. `reconnect` is `True` if this is a reconnection.
- `on_lyra_node_disconnected(node_id, is_nodelink, player_count)` — Fired when a node disconnects.
- `on_lyra_node_reconnecting(node_id, is_nodelink, retry_in)` — Fired when Lyra is attempting to reconnect to a node. `retry_in` is the delay in seconds.

### NodeLink-specific events

The following events are only dispatched by NodeLink instances:

- `on_lyra_player_created(player, guild_id)` — Fired when a player is created for a guild.
- `on_lyra_volume_changed(player, volume)` — Fired when the player volume changes.
- `on_lyra_player_connected(player, voice)` — Fired when the player connects to a voice channel. `voice` is the raw `dict[str, Any]` payload, not a `VoiceChannel`/`VoiceState`.
- `on_lyra_filters_changed(player, filters)` — Fired when the player's audio filters change. `filters` is the raw `dict[str, Any]` payload, not a `Filters` instance.
- `on_lyra_pause(player, paused)` — Fired when the player is paused or resumed. `paused` is a `bool`.
- `on_lyra_seek(player, position)` — Fired when the player seeks. `position` is the new position in milliseconds.
- `on_lyra_mix_started(player, mix_id, track, volume)` — Fired when a mix layer starts. `mix_id` identifies the mix layer, `track` is the `Track` being mixed in (or `None`), and `volume` is the mix layer's volume (`0.0`–`1.0`).
- `on_lyra_mix_ended(player, mix_id, reason)` — Fired when a mix layer ends. `reason` is a `MixEndReason` enum (`FINISHED`, `REMOVED`, `ERROR`, or `MAIN_ENDED`). The event also exposes `is_finished`, `is_removed`, `is_error`, and `is_main_ended` boolean properties as shortcuts for checking `reason`.
