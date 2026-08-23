# Frequently Asked Questions

> Why is it saying "Cannot connect to host"?

Here are some common causes, in order of likelihood:
- You don't have a Lavalink node (or NodeLink instance) running.
- The `host`/`port` passed to `NodePool.create_node()` don't match where your node is
  actually listening — for example using `localhost` when the node is in a Docker
  container on a different network.
- The node is reachable but a firewall, VPN, or Docker network rule is blocking the
  connection.

If you don't have a Lavalink node yet, download it [here.](https://github.com/lavalink-devs/Lavalink/releases/latest)
For everything else, double-check the values above against your node's config and logs first — most "Cannot connect to host" errors come from a host/port mismatch or the node not running.

:::{note}

A `password` mismatch is reported as a generic `NodeConnectionFailure` (`"Failed to establish initial connection to node '...'"`), since the node rejects the initial REST version check before the websocket handshake is ever attempted.

:::

> What experience do I need?

This library assumes that you have some experience with Python, asynchronous programming, and the discord.py or py-cord library.

> How do I install Lyra?

Refer to the [Installation](installation.md) section.

> How do I use Lyra?

If you want a quick example, refer to the [Quickstart](quickstart.md) section.

For step-by-step walkthroughs of specific tasks (playing tracks, filters, queues, events, etc.),
refer to the [How Do I?](hdi/index.md) section.

If you are interested in the full class/method reference, refer to the [API Reference](api/index.md) section.

> How do I add Spotify or Apple Music support?

Lyra does not handle Spotify/Apple Music credentials directly. Platform support is managed entirely by your Lavalink server via plugins. Install [LavaSrc](https://github.com/topi314/LavaSrc) on your Lavalink server and configure your API credentials in `application.yml`.

> How do I use the LavaSearch plugin?

Install the [LavaSearch](https://github.com/topi314/LavaSearch) plugin on your Lavalink server, then pass `search=True` when calling `NodePool.create_node()`. See the [LavaSearch guide](hdi/search.md) for details.

> How do I fetch song lyrics?

Lyrics are supported via the Lavalink v4 lyrics endpoint or via NodeLink. See the [Lyrics guide](hdi/lyrics.md) for details.

> Is Lyra compatible with both discord.py and py-cord?

Yes. Lyra is compatible with both discord.py (2.6.0+) and py-cord (2.8.0+). The `compat` module handles minor API differences automatically.

> I was previously using Pomice. What changed?

Lyra is a full refactor of Pomice for Lavalink v4. Key changes:
- Import `lava_lyra` instead of `pomice`
- No more Spotify/Apple Music credentials in `create_node()` — use server-side plugins
- Event names use the `on_lyra_*` prefix instead of `on_pomice_*`
- New features: lyrics support, LavaSearch, advanced filter management, NodeLink support

> What's the difference between Lavalink and NodeLink?

Lavalink is the original Java-based audio delivery server. [NodeLink](https://github.com/PerformanC/NodeLink)
is a compatible reimplementation (JavaScript/TypeScript) that speaks a mostly-compatible protocol,
plus a handful of extra features Lavalink doesn't have (gapless playback, mix layers, extra
filters, and more granular player-state events). Lyra works with either.

> How does Lyra know if I'm connected to Lavalink or NodeLink?

Automatically. When a node connects, Lyra checks the `isNodelink` field returned by the node's
`/v4/info` endpoint and sets `Node._is_nodelink` accordingly — there's no config flag to set.
This also determines which minimum version is required (Lavalink 4.2.0+ vs NodeLink 3.2.0+).

> Which features are NodeLink-only?

The `gapless` parameter on `Player.play()`/`Player.stop()`, mix layers (`MixStartedEvent`/`MixEndedEvent`),
the `Chorus`/`Compressor`/`Echo`/`Highpass`/`Phaser`/`Spatial` filters, and the
`PlayerCreatedEvent`/`VolumeChangedEvent`/`PlayerConnectedEvent`/`FiltersChangedEvent`/`PauseEvent`/`SeekEvent`
events are all NodeLink-only. Calling NodeLink-only filters or the `gapless` parameter against a
plain Lavalink node raises `NodelinkExclusive` client-side before the request is even sent.

The route planner API (`Node.route_planner`) works against both — NodeLink implements the same
`routeplanner/status`, `routeplanner/free/address`, and `routeplanner/free/all` endpoints as
Lavalink, at the same paths.

> Can I mix Lavalink and NodeLink nodes in the same `NodePool`?

Yes. NodeLink/Lavalink detection happens per-node, so you can run both kinds side by side in the
same pool. Just be aware that NodeLink-only functionality (see above) will raise `NodelinkExclusive`
if it happens to run against a player on a plain Lavalink node.
