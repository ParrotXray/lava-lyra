# Use the Node class

The `Node` class is one of the main classes you will be interacting with when using Lyra.

It has a number of functions you will be using frequently:

- `Node.get_player()`
- `Node.get_tracks()`
- `Node.get_recommendations()`
- `Node.build_track()`
- `Node.connect()`
- `Node.enable()`
- `Node.disable()`
- `Node.disconnect()`
- `Node.send()`
- `Node.load_search()`


There are also properties the `Node` class has to access certain values:

:::{list-table}
:header-rows: 1

* - Property
  - Type
  - Description

* - `Node.bot`
  - `discord.Bot` (Py-cord) / `commands.Bot` (Discord.py)
  - Returns the bot instance linked to this node.

* - `Node.identifier`
  - `str`
  - Returns this node's identifier.

* - `Node.enabled`
  - `bool`
  - Returns whether this node is currently enabled.

* - `Node.lyrics_enabled`
  - `bool`
  - Returns whether lyrics support is enabled for this node.

* - `Node.search_enabled`
  - `bool`
  - Returns whether LavaSearch plugin support is enabled for this node.

* - `Node.health_monitor`
  - `NodeHealthMonitor`
  - Returns the node's health monitor.

* - `Node.health_score`
  - `float`
  - Returns the node's current health score, based on latency, uptime, player load, and connection stability. Used by `NodeAlgorithm.by_health`.

* - `Node.route_planner`
  - `RoutePlanner`
  - Returns the node's route planner, used to manage banned IP addresses for the route planner API (Lavalink or NodeLink).

* - `Node.is_connected`
  - `bool`
  - Returns whether this node is connected or not.

* - `Node.latency` `Node.ping`
  - `float`
  - Returns the latency of the node, or `-1.0` if no probe has completed yet or the last probe
    failed (e.g. the node dropped and hasn't reconnected). Whatever the last probe wrote — good
    or `-1.0` — stays cached until the next probe runs.

* - `Node.player_count`
  - `int`
  - Returns how many players are connected to this node.

* - `Node.players`
  - `Dict[int, Player]`
  - Returns a dict containing the guild ID and the player object.

* - `Node.pool`
  - `type[NodePool]`
  - Returns the `NodePool` class this node is part of. `NodePool` is a classmethod-only container, not instantiated.

* - `Node.stats`
  - `NodeStats`
  - Returns the nodes stats.

:::

`NodeStats` has the following attributes:

:::{list-table}
:header-rows: 1

* - Attribute
  - Type
  - Description

* - `used`
  - `Optional[int]`
  - Memory used by the node.

* - `free`
  - `Optional[int]`
  - Free memory available to the node.

* - `reservable`
  - `Optional[int]`
  - Reservable memory.

* - `allocated`
  - `Optional[int]`
  - Allocated memory.

* - `cpu_cores`
  - `Optional[int]`
  - Number of CPU cores available to the node.

* - `cpu_system_load`
  - `Optional[float]`
  - System-wide CPU load.

* - `cpu_process_load`
  - `Optional[float]`
  - CPU load caused by the node process itself.

* - `players_total`
  - `int`
  - Total number of players on the node.

* - `players_active`
  - `int`
  - Number of players currently playing.

* - `uptime`
  - `Optional[int]`
  - Node uptime, in milliseconds.

:::

## Getting a player

To get a player from the nodes list of players, we need to use `Node.get_player()`

```py
Node.get_player(...)
```

After you have initialized your function, you need to specify the `guild_id` of the player.

```py

Node.get_player(guild_id=<your guild ID here>)

```

If the node finds a player with the guild ID you provided, it'll return the [](../api/player.md) object associated with the guild ID.


## Getting tracks

To get tracks using Lavalink, we need to use `Node.get_tracks()`

You can also use `Player.get_tracks()` to do the same thing, but this can be used to fetch tracks regardless if a player exists.

```py
await Node.get_tracks(...)
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

await Node.get_tracks(
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

This returns a `Playlist` if `query` resolved to a playlist, a `list[Track]` for individual
tracks, or `None` if nothing was found — check which you got with `isinstance()` before
iterating. Raises `TrackLoadError` if the node reports a load failure.
Ideally, you should be putting all tracks into some sort of a queue. If you would like to learn about how to use
our queue implementation, you can refer to [](queue.md)


## Building a track from an identifier

If you already have a valid Lavalink track identifier and want to turn it back into a `Track`
object without running a new search, use `Node.build_track()`

You can also use `Player.build_track()` to do the same thing, but this can be used regardless
of whether a player exists.

```py
await Node.build_track(...)
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

await Node.build_track(
    identifier="<your track identifier here>",
    ctx=<optional ctx object here>,
)

```

## Connecting a node

`NodePool.create_node()` already calls `Node.connect()` for you, so most of the time you won't
call this directly.

```py
await Node.connect()
```

The `reconnect` kwarg is for Lyra's own internal reconnect loop — it skips the initial
version/handshake check since the node was already validated on first connect. You won't
need to pass it yourself; to manually bring a disconnected node back, use `Node.enable()`
instead (see below).

## Enabling and disabling a node

To temporarily take a node out of rotation without removing it from the pool, we use
`Node.disable()`. To bring it back, we use `Node.enable()`

```py
await Node.disable()
```

Disabling a node closes its websocket connection and stops it from being selected by
`NodePool.get_best_node()` or a random `NodePool.get_node()` call.

```py
await Node.enable()
```

Enabling a node reconnects it if it isn't already connected, so it can be selected again.

## Disconnecting a node

To fully disconnect a node and remove it from the pool (destroying any players connected to
it in the process), use `Node.disconnect()`

```py
await Node.disconnect()
```

Unlike `Node.disable()`, this is not reversible — the node is removed from `NodePool` entirely
and must be re-added with `NodePool.create_node()` if you need it again.

## Sending raw requests

`Node.send()` is a low-level escape hatch that issues a raw HTTP request to the node's
REST API (`method`, `path`, `guild_id`, `data`, etc.), for hitting endpoints Lyra doesn't
wrap yet. Most users won't need this — prefer the typed methods on `Node`/`Player` instead.

```py
await Node.send(
    method="GET",
    path="stats",
)
```

:::{important}

Raises `NodeNotAvailable` if the node isn't available, has no active HTTP session (call
`Node.connect()` first), or the underlying request fails at the connection level. Endpoints
under `sessions/` also require an active session ID. Raises `NodeRestException` if the server
responds with a non-2xx status or a non-JSON body.

:::

## Searching with LavaSearch

If the node has the LavaSearch plugin installed (check `Node.search_enabled`), you can search
for tracks, albums, artists, playlists, and text in a single call using `Node.load_search()`

```py
result = await node.load_search(query="<your query here>", types=[<LavaSearchType values here>])
```

This returns a `SearchResult` (or `None` if nothing was found) grouping the matched tracks,
albums, artists, playlists, and text results by type. See [](search.md) for the full parameter
table, `SearchResult`, `LavaSearchType`, and the exceptions this raises.

## Monitoring node health

`Node.health_monitor` returns a `NodeHealthMonitor`, which tracks a node's reliability over time
and backs the `NodeAlgorithm.by_health` selection algorithm. It has a few things you'll use:

:::{list-table}
:header-rows: 1

* - Member
  - Description

* - `NodeHealthMonitor.get_health_score(current_latency, player_count)`
  - Computes a health score from the given latency and player count. `Node.health_score` calls this for you with the node's current values.

* - `NodeHealthMonitor.is_circuit_open`
  - `bool` property. `True` if the circuit breaker has tripped (the node is being treated as unhealthy and temporarily skipped).

* - `NodeHealthMonitor.check_circuit_breaker()`
  - Opens the circuit breaker if consecutive failures reached the threshold. This can only open the circuit — closing happens via `record_success()`, or lazily the next time `is_circuit_open` is read after the timeout has elapsed.

* - `NodeHealthMonitor.record_success()`
  - Records a successful request/operation against the node, improving its health score over time.

* - `NodeHealthMonitor.record_failure()`
  - Records a failed request/operation against the node, degrading its health score and contributing toward tripping the circuit breaker.

* - `NodeHealthMonitor.record_reconnection()`
  - Records that the node reconnected after a disconnect, factored into its stability score.

* - `NodeHealthMonitor.quality_tracker`
  - The underlying `ConnectionQualityTracker` object used to compute connection-quality statistics.

:::

`ConnectionQualityTracker` (`NodeHealthMonitor.quality_tracker`) itself exposes:

:::{list-table}
:header-rows: 1

* - Member
  - Description

* - `ConnectionQualityTracker.record_reconnection()`
  - Records a reconnection event.

* - `ConnectionQualityTracker.record_connection_success()`
  - Records a successful connection.

* - `ConnectionQualityTracker.record_connection_failure()`
  - Records a connection failure.

* - `ConnectionQualityTracker.record_latency(latency)`
  - Records a latency sample, used to compute `average_latency`.

* - `ConnectionQualityTracker.average_latency`
  - `float` property. Average of recent latency samples, or `-1.0` if none have been recorded.

* - `ConnectionQualityTracker.uptime_percentage`
  - `float` property. Percentage of time connected since tracking started.

* - `ConnectionQualityTracker.reconnection_count`
  - `int` property. Total number of recorded reconnections.

* - `ConnectionQualityTracker.consecutive_failures`
  - `int` property. Current streak of consecutive connection failures.

* - `ConnectionQualityTracker.is_stable`
  - `bool` property. `True` if there are no consecutive failures, uptime is above 95%, and average latency is under 1000ms (or no samples yet).

:::

You will rarely need to call these directly — Lyra's internal reconnect and node-selection logic
already uses them. They're most useful if you're building your own custom node-selection
algorithm or want to expose node health in a dashboard/status command.

```py
node = NodePool.get_node(identifier="MAIN")
print(f"Health score: {node.health_score}")
print(f"Circuit open: {node.health_monitor.is_circuit_open}")
```

## Getting recommendations

To get recommendations using Lavalink, we need to use `Node.get_recommendations()`

You can also use `Player.get_recommendations()` to do the same thing, but this can be used to fetch recommendations regardless if a player exists.

```py
await Node.get_recommendations(...)
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

await Node.get_recommendations(
    track=<your track object here>,
    ctx=<optional ctx object here>,
)

```

Recommendations are only supported for Spotify, Deezer, Tidal, JioSaavn, YouTube, and YouTube
Music tracks —
`Node.get_recommendations()` raises `TrackLoadError` for any other `track_type`, and `TypeError`
if `track` is `None`. When the source
is supported, this returns whatever the underlying search would: a `list[Track]`, a `Playlist`
(e.g. YouTube's autoplay radio can resolve to one), or `None` if the search came back empty —
check which you got with `isinstance()` before iterating.
Ideally, you should be putting all tracks into some sort of a queue. If you would like to learn about how to use
our queue implementation, you can refer to [](queue.md)

## Managing the route planner

:::{note}

The route planner API is used for IP rotation to avoid YouTube/source bans, and works on both
Lavalink and NodeLink nodes — NodeLink implements the same `routeplanner/status`,
`routeplanner/free/address`, and `routeplanner/free/all` endpoints at the same paths. It must be
configured on your node first (`application.yml` for Lavalink, `network.routePlanner` in
`config.ts` for NodeLink) before any of these calls will return meaningful data. If it isn't
configured, `get_status()` will raise a `NodeRestException`.

:::

If your node has IP rotation configured, `Node.route_planner` gives
you a `RoutePlanner` to check its status and manage banned/failing addresses.

```py
route_planner = node.route_planner
```

`RoutePlanner.node` holds a reference back to the owning `Node`.

### Getting the route planner status

```py
status = await route_planner.get_status()
```

This returns a `RouteStats` object with the following attributes:

:::{list-table}
:header-rows: 1

* - Attribute
  - Type
  - Description

* - `strategy`
  - `Optional[RouteStrategy]`
  - The route planner strategy in use (e.g. rotating IP, nano IP), or `None` if it couldn't be parsed.

* - `ip_block_type`
  - `Optional[RouteIPType]`
  - The type of IP block configured (`RouteIPType.IPV4` or `RouteIPType.IPV6`), or `None` if it couldn't be parsed.

* - `ip_block_size`
  - `Optional[str | int]`
  - The size of the configured IP block. Lavalink returns a string, NodeLink returns an int.

* - `failing_addresses`
  - `List[FailingIPBlock]`
  - Addresses currently marked as failing, along with when they failed.

* - `block_index`
  - `Optional[str]`
  - The current block index.

* - `address_index`
  - `Optional[str]`
  - The current address index.

:::

Each entry in `failing_addresses` is a `FailingIPBlock` object:

:::{list-table}
:header-rows: 1

* - Attribute
  - Type
  - Description

* - `address`
  - `Optional[str]`
  - The failing address.

* - `failing_time`
  - `datetime`
  - When the address was marked as failing.

:::

### Freeing a failing address

To manually mark a specific address as no longer failing, use `RoutePlanner.free_address()`

```py
await route_planner.free_address(ip="<the failing address here>")
```

### Freeing all failing addresses

To clear every address currently marked as failing, use `RoutePlanner.free_all_addresses()`

```py
await route_planner.free_all_addresses()
```
