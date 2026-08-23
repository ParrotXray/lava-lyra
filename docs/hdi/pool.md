# Use the NodePool class

The `NodePool` class is the first class you will use when using Lyra.

:::{important}

`NodePool` has `__slots__ = ()` and is used entirely through its classmethods — you never
instantiate it. Always call `NodePool.create_node(...)`, `NodePool.get_node(...)`, etc.
directly on the class, **not** on `NodePool()`.

:::

The `NodePool` Class has four main functions you can use:

- `NodePool.create_node()`
- `NodePool.get_node()`
- `NodePool.get_best_node()`
- `NodePool.disconnect()`


## Adding a node

To add a node to our `NodePool`, we need to run `NodePool.create_node()`.

```py
await NodePool.create_node(...)
```

After you have initialized your function, we need to fill in the proper parameters:


:::{list-table}
:header-rows: 1

* - Name
  - Type
  - Description

* - `bot`
  - `BotType`
  - A Discord.py or Py-cord `Client` object (can be either a `Client` or a `commands.Bot`)

* - `host`
  - `str`
  - The IP/URL of your Lavalink node. Remember not to include the port in this field

* - `port`
  - `int`
  - The port your Lavalink node uses. By default, Lavalink uses `2333`.

* - `identifier`
  - `str`
  - The identifier your `Node` object uses to distinguish itself.

* - `password`
  - `str`
  - The password used to connect to your node.

* - `enabled`
  - `bool`
  - Set this value to `True` to enable this node. If you set this to `False`, the node will be added to the pool but will not be used. `Node.enabled` is read-only after creation — use `await Node.enable()` / `await Node.disable()` to change it.

* - `search`
  - `bool`
  - Set this value to `True` to enable [LavaSearch](https://github.com/topi314/LavaSearch) plugin support on this node. Requires the plugin to be installed on your Lavalink server.

* - `fallback`
  - `bool`
  - Set this value to `True` if you want Lyra to automatically switch all players to another available node if one disconnects.
    You must have two or more nodes to be able to do this.

* - `logger`
  - `Optional[logging.Logger]`
  - If you would like to receive logging information from Lyra, set this to your logger class

* - `secure`
  - `bool`
  - Set this value to `True` to connect to your node over `wss`/`https` instead of `ws`/`http`. Default value is `False`.

* - `heartbeat`
  - `int`
  - The interval (in seconds) between websocket heartbeat pings. Default value is `120`.

* - `resume_key`
  - `Optional[str]`
  - A key used by Lavalink to resume a session after a disconnect, preserving players. Default value is `None` (resuming disabled).

* - `resume_timeout`
  - `int`
  - How long (in seconds) Lavalink should keep a session resumable for after a disconnect. Default value is `60`.

* - `loop`
  - `Optional[asyncio.AbstractEventLoop]`
  - The event loop to run the node on. Default value is `None`, which uses the currently running loop.

* - `session`
  - `Optional[aiohttp.ClientSession]`
  - An existing `aiohttp.ClientSession` to reuse for this node's REST traffic (the websocket connection uses a separate `websockets` connection). Default value is `None`, which creates a new session.

* - `lyrics`
  - `bool`
  - Set this value to `True` to enable lyrics support on this node. Requires a lyrics-capable plugin (or NodeLink) on the server. Default value is `False`.

* - `circuit_breaker_threshold`
  - `int`
  - Number of consecutive failures before the circuit breaker opens for this node. Default value is `5`. For foreign/unstable nodes, consider increasing to `10`-`20`.

* - `circuit_timeout`
  - `float`
  - Seconds to keep the circuit open before retrying. Default value is `60.0`. For foreign nodes, consider increasing to `120.0` or more.

* - `connect_timeout`
  - `float`
  - Timeout in seconds for establishing the initial connection. Default value is `10.0`. For foreign nodes with high latency, consider increasing to `30.0`-`60.0`.

* - `total_timeout`
  - `float`
  - Timeout in seconds applied to every REST request made over this node's persistent session (not just the initial connection). Default value is `30.0`.

:::

After you set those parameters, your function should look something like this:

```py

await NodePool.create_node(
    bot=bot,
    host="<your ip here>",
    port=<your port here>,
    identifier="<your id here>",
    password="<your password here>",
    enabled=<True/False>,
    search=<True/False>,
    fallback=<True/False>,
    logger=<your logger here>
)

```
:::{note}

Platform support (Spotify, Apple Music, Deezer, etc.) is handled entirely by your Lavalink server's plugins — no credentials are needed in Lyra. Install [LavaSrc](https://github.com/topi314/LavaSrc) on your server and configure it in `application.yml`.

:::

:::{important}

Raises `NodeCreationError` if `identifier` is already in use, or if `bot.user` isn't ready yet
(call this after your bot has logged in). Raises `LavalinkVersionIncompatible` if the node's
Lavalink/NodeLink version is below the minimum supported. Raises `NodeConnectionFailure` if
the node can't be reached, or if `password` doesn't match the node's configured password.

:::

Now that you have your Node object created, move on to [Using a node](node.md) to see what you can do with your `Node` object.

## Getting a node

To get a node from the node pool, we need to use `NodePool.get_node()`

```py
NodePool.get_node(...)
```

After you have initialized your function, you can specify a identifier if you want to grab a specified node:

```py
NodePool.get_node(identifier="<your id here>")
```

If you do not set a identifier, it'll return a random node from the pool.

:::{important}

Raises `NoNodesAvailable` if no nodes are currently available, or if `identifier` doesn't
match any available node.

:::

:::{tip}

You can check how many nodes are currently registered in the pool with `NodePool.node_count`, and
get the full `Dict[str, Node]` mapping (keyed by identifier) with `NodePool.nodes`.

:::

## Getting the best node

To get a node from the node pool based on certain requirements, we need to use `NodePool.get_best_node()`

```py
NodePool.get_best_node(...)
```

After you have initialized your function, you need to specify a `NodeAlgorithm` to use to grab your node from the pool.
The available algorithms are `by_ping`, `by_total_players`, `by_playing_players`, and `by_health`.
If you want to view what they do, refer to the `NodeAlgorithm` enum in the [](../api/enums.md) section.

```py
NodePool.get_best_node(algorithm=NodeAlgorithm.xyz)
```

:::{important}

Raises `NoNodesAvailable` if no nodes are currently available, or `ValueError` if `algorithm`
isn't a valid `NodeAlgorithm`.

:::

## Disconnecting all nodes from the pool

To disconnect all nodes from the pool, we need to use `NodePool.disconnect()`

```py
await NodePool.disconnect()
```

Unlike `Node.disable()`, this is not reversible — every node is removed from the pool entirely
(destroying any players still connected to them) and must be re-added with `NodePool.create_node()`.
