# Frequently Asked Questions

> Why is it saying "Cannot connect to host"?

Here are some common issues:
- You don't have a Lavalink node installed
- You have a Lavalink node, but it's not configured properly
- You have a Lavalink node and it's configured properly, but is unreachable due to firewall rules or a malformed network configuration.

If you are experiencing the first issue, you can download Lavalink [here.](https://github.com/lavalink-devs/Lavalink/releases/latest)

As for the other listed issues, either consult the Lavalink docs or go through the proper support channels for your specific issue at hand.

For any other issues not listed here, please consult your preferred resource for more information.

> What experience do I need?

This library assumes that you have some experience with Python, asynchronous programming, and the discord.py or py-cord library.

> How do I install Lyra?

Refer to the [Installation](installation.md) section.

> How do I use Lyra?

If you are interested in learning how Lyra works, refer to the [API Reference](api/index.md) section.

If you want a quick example, refer to the [Quickstart](quickstart.md) section.

> How do I add Spotify or Apple Music support?

Lyra does not handle Spotify/Apple Music credentials directly. Platform support is managed entirely by your Lavalink server via plugins. Install [LavaSrc](https://github.com/topi314/LavaSrc) on your Lavalink server and configure your API credentials in `application.yml`.

> How do I use the LavaSearch plugin?

Install the [LavaSearch](https://github.com/topi314/LavaSearch) plugin on your Lavalink server, then pass `search=True` when calling `NodePool.create_node()`. See the [LavaSearch guide](hdi/search.md) for details.

> How do I fetch song lyrics?

Lyrics are supported via the Lavalink v4 lyrics endpoint or via NodeLink. See the [Lyrics guide](hdi/lyrics.md) for details.

> Is Lyra compatible with both discord.py and py-cord?

Yes. Lyra is compatible with both `discord.py` (v2+) and `py-cord` (v2+). The `compat` module handles minor API differences automatically.

> I was previously using Pomice. What changed?

Lyra is a full refactor of Pomice for Lavalink v4. Key changes:
- Import `lava_lyra` instead of `pomice`
- No more Spotify/Apple Music credentials in `create_node()` — use server-side plugins
- Event names use the `on_lyra_*` prefix instead of `on_pomice_*`
- New features: lyrics support, LavaSearch, advanced filter management, NodeLink support
