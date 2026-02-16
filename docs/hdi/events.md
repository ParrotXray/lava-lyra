# Use the Events class

Lyra has different events that are triggered depending on events emitted by Lavalink or the library itself.

Here is the full list of events:

- `TrackStartEvent` → `on_lyra_track_start`
- `TrackEndEvent` → `on_lyra_track_end`
- `TrackStuckEvent` → `on_lyra_track_stuck`
- `TrackExceptionEvent` → `on_lyra_track_exception`
- `WebsocketClosedEvent` → `on_lyra_websocket_closed`
- `WebsocketOpenEvent` → `on_lyra_websocket_open`
- `LyricsFoundEvent` → `on_lyra_lyrics_found`
- `LyricsUnavailableEvent` → `on_lyra_lyrics_unavailable`
- `LyricsUpdateEvent` → `on_lyra_lyrics_update`
- `NodeConnectedEvent` → `on_lyra_node_connected`
- `NodeDisconnectedEvent` → `on_lyra_node_disconnected`
- `NodeReconnectingEvent` → `on_lyra_node_reconnecting`
- `PlayerCreatedEvent` → `on_lyra_player_created`
- `VolumeChangedEvent` → `on_lyra_volume_changed`
- `PlayerConnectedEvent` → `on_lyra_player_connected`
- `FiltersChangedEvent` → `on_lyra_filters_changed`

Here is an example of how you would listen for the `TrackStartEvent` within a cog:

```py
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
- `on_lyra_track_exception(player, track, error)` — Fired when a track fails to play. `error` is a string in the format `REASON: [SEVERITY]`.

### Websocket events

- `on_lyra_websocket_closed(payload)` — Fired when the websocket connection is closed. `payload` contains the `Guild`, close code, reason, and whether the close was remote.
- `on_lyra_websocket_open(target, ssrc)` — Fired when the websocket connection is opened. `target` is the node's IP and `ssrc` is the 32-bit integer identifying the RTP stream.

### Lyrics events

- `on_lyra_lyrics_found(player, track, lyrics)` — Fired when lyrics are found for the current track. `lyrics` is a `Lyrics` object.
- `on_lyra_lyrics_unavailable(player, track)` — Fired when lyrics are not available for the current track.
- `on_lyra_lyrics_update(player, track, line)` — Fired when the current lyric line changes (live lyrics subscription). `line` is a `LyricLine` object.

### Node events

- `on_lyra_node_connected(node_id, is_nodelink, reconnect)` — Fired when a node connects. `reconnect` is `True` if this is a reconnection.
- `on_lyra_node_disconnected(node_id, is_nodelink, player_count)` — Fired when a node disconnects.
- `on_lyra_node_reconnecting(node_id, is_nodelink, retry_in)` — Fired when Lyra is attempting to reconnect to a node. `retry_in` is the delay in seconds.

### Player state events

- `on_lyra_player_created(player, guild_id)` — Fired when a player is created for a guild.
- `on_lyra_volume_changed(player, volume)` — Fired when the player volume changes.
- `on_lyra_player_connected(player, voice)` — Fired when the player connects to a voice channel.
- `on_lyra_filters_changed(player, filters)` — Fired when the player's audio filters change.
