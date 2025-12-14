# Lyra

[![PyPI](https://img.shields.io/pypi/v/lava-lyra.svg)](https://pypi.org/project/lava-lyra/)
[![downloads](https://img.shields.io/pypi/dm/lava-lyra.svg)](https://pypi.org/project/lava-lyra/)
[![Python](https://img.shields.io/pypi/pyversions/lava-lyra.svg)](https://pypi.org/project/lava-lyra/)
[![License](https://img.shields.io/github/license/ParrotXray/lava-lyra.svg)](https://github.com/ParrotXray/Lyra/blob/main/LICENSE)

A modern Lavalink v4 wrapper designed for py-cord, based on the excellent [Pomice](https://github.com/cloudwithax/pomice) library by cloudwithax.

## What's New in Lyra

Lyra is a complete refactor of Pomice for **Lavalink v4.X or NodeLink v3.X**, bringing significant improvements:

- **Full Lavalink v4 REST API support**
- **Server-side plugin integration** (LavaSrc, YouTube plugin, etc.)
- **Simplified setup** - No more API credentials needed in client
- **Better error handling** and plugin support  
- **Removed deprecated modules** (client-side Spotify/Apple Music parsing)
- **Optimized for py-cord** instead of discord.py
- **Improved documentation** and examples

## Key Differences from Pomice

| Feature | Pomice (v2.x) | Lyra (v1.x) |
|---------|---------------|-------------|
| Lavalink Support | v3.x & v4.x | **v4.x** |
| Nodelink Support | Unknown | **v3.x** |
| Discord Library | discord.py | **py-cord** |
| Spotify Support | Client-side API | **Server plugin** |
| Apple Music Support | Client-side API | **Server plugin** |
| Setup Complexity | API keys required | **Plugin configuration only** |
| Architecture | Mixed client/server | **Pure server-side** |

## Quick Start

### Installation

```bash
pip install lava_lyra
```

### Basic Usage

```python
import discord
import lava_lyra

class Bot(discord.Bot):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.node = None

    async def on_ready(self):
        print(f'Logged in as {self.user}')

        # Create Lavalink nodes - much simpler than before!
        node = await lava_lyra.NodePool.create_node(
          bot=self,
          host='localhost',
          port=2333,
          password='youshallnotpass',
          identifier='MAIN',
          lyrics=False,
          lavasearch=True,  # Enable LavaSearch plugin support
          fallback=True,
        )
        print(f"Created node: {node.identifier}")

bot = Bot()
bot.run('your_bot_token')
```

### Playing Music

```python
@bot.slash_command(description="Play music")
async def play(ctx, query: str):
    # Connect to voice channel
    if not ctx.author.voice:
        return await ctx.respond("You need to be in a voice channel!")
    
    player = await ctx.author.voice.channel.connect(cls=lava_lyra.Player)
    
    # Search for tracks (supports Spotify, YouTube, Apple Music via plugins!)
    results = await player.get_tracks(query)
    
    if not results:
        return await ctx.respond("No tracks found!")
    
    # Play the track
    track = results[0]
    await player.play(track)
    await ctx.respond(f"Now playing: **{track.title}**")
```

### Advanced Search with LavaSearch

LavaSearch plugin provides advanced search capabilities across tracks, albums, artists, playlists, and text suggestions.

**Important:** You must enable LavaSearch when creating the node by setting `search=True`:

```python
node = await lava_lyra.NodePool.create_node(
    bot=bot,
    host='localhost',
    port=2333,
    password='youshallnotpass',
    identifier='MAIN',
    search=True  # Enable LavaSearch support
)
```

```python
@bot.slash_command(description="Search for music")
async def search(ctx, query: str, platform: str = "youtube"):
    # Get the node
    node = lava_lyra.NodePool.get_node()

    # Map platform to search type
    search_types = {
        "youtube": lava_lyra.SearchType.ytsearch,
        "spotify": lava_lyra.SearchType.spsearch,
        "soundcloud": lava_lyra.SearchType.scsearch,
        "apple_music": lava_lyra.SearchType.amsearch,
    }

    # Search for tracks, albums, artists, playlists, and text
    result = await node.load_search(
        query=query,
        types=[
            lava_lyra.LavaSearchType.TRACK,
            lava_lyra.LavaSearchType.ALBUM,
            lava_lyra.LavaSearchType.ARTIST,
            lava_lyra.LavaSearchType.PLAYLIST,
            lava_lyra.LavaSearchType.TEXT
        ],
        search_type=search_types.get(platform, lava_lyra.SearchType.ytsearch),
        ctx=ctx
    )

    if not result:
        return await ctx.respond("No results found!")

    # Display results
    response = [f"**Search results for '{query}' on {platform}:**\n"]

    if result.tracks:
        response.append(f"**Tracks ({len(result.tracks)}):**")
        for track in result.tracks[:3]:  # Show first 3
            response.append(f"  - {track.title} by {track.author}")

    if result.albums:
        response.append(f"\n**Albums ({len(result.albums)}):**")
        for album in result.albums[:3]:
            response.append(f"  - {album.name}")

    if result.artists:
        response.append(f"\n**Artists ({len(result.artists)}):**")
        for artist in result.artists[:3]:
            response.append(f"  - {artist.name}")

    if result.playlists:
        response.append(f"\n**Playlists ({len(result.playlists)}):**")
        for playlist in result.playlists[:3]:
            response.append(f"  - {playlist.name}")

    if result.texts:
        response.append(f"\n**Suggestions:**")
        for text in result.texts[:5]:
            response.append(f"  - {text.text}")

    await ctx.respond("\n".join(response))
```

**Note:** The LavaSearch plugin must be installed on your Lavalink server for this feature to work. See the server setup section below.

## Lavalink v4 Server Setup

Lyra requires a Lavalink v4 server with plugins. Here's a basic `application.yml`:

```yaml
server:
  port: 2333
  address: 127.0.0.1

lavalink:
  plugins:
    # Required for YouTube support
    - dependency: "dev.lavalink.youtube:youtube-plugin:VERSION"
    - repository: "https://maven.lavalink.dev/releases"

    # Required for Spotify, Apple Music, Deezer, etc.
    - dependency: "com.github.topi314.lavasrc:lavasrc-plugin:VERSION"
      repository: "https://maven.lavalink.dev/releases"

    # Optional: LavaSearch for advanced search functionality
    - dependency: "com.github.topi314.lavasearch:lavasearch-plugin:VERSION"
      repository: "https://maven.lavalink.dev/releases"

  server:
    password: "youshallnotpass"

plugins:
  youtube:
    enabled: true
    allowSearch: true

  lavasrc:
    sources:
      spotify: true
      applemusic: true
      deezer: true
    
    spotify:
      clientId: "your_spotify_client_id"
      clientSecret: "your_spotify_client_secret"
      countryCode: "US"
```

## Supported Platforms

All platforms are now supported via Lavalink server plugins:

- **YouTube** - via [YouTube](https://github.com/lavalink-devs/youtube-source) plugin
- **Spotify** - via [LavaSrc](https://github.com/topi314/LavaSrc) plugin
- **Apple Music** - via [LavaSrc](https://github.com/topi314/LavaSrc) plugin
- **Bilibili** - via [Lavabili](https://github.com/ParrotXray/lavabili-plugin) plugin
- **SoundCloud** - built-in [Lavalink](https://github.com/lavalink-devs/Lavalink)
- **And many more** via community plugins!

## LavaSearch Plugin Support

Lyra now includes full support for the [LavaSearch](https://github.com/topi314/LavaSearch) plugin, which provides advanced search capabilities:

### Features

- **Multi-type Search**: Search for tracks, albums, artists, playlists, and text suggestions in a single query
- **Rich Results**: Get comprehensive search results with detailed metadata
- **Plugin Integration**: Works seamlessly with LavaSrc and other Lavalink plugins

### Installation

Add LavaSearch to your Lavalink server's `application.yml`:

```yaml
lavalink:
  plugins:
    - dependency: "com.github.topi314.lavasearch:lavasearch-plugin:x.y.z"
      repository: "https://maven.lavalink.dev/releases"
```

Replace `x.y.z` with the [latest version](https://github.com/topi314/LavaSearch/releases).

**Example:**

```python
# Search YouTube for everything
result = await node.load_search(
    query="architects animals",
    types=[
        lava_lyra.LavaSearchType.TRACK,
        lava_lyra.LavaSearchType.ALBUM,
        lava_lyra.LavaSearchType.ARTIST,
        lava_lyra.LavaSearchType.PLAYLIST,
        lava_lyra.LavaSearchType.TEXT
    ],
    search_type=lava_lyra.SearchType.ytsearch
)

# Search Spotify for tracks and artists
result = await node.load_search(
    query="metallica",
    types=[
        lava_lyra.LavaSearchType.TRACK,
        lava_lyra.LavaSearchType.ARTIST
    ],
    search_type=lava_lyra.SearchType.spsearch
)

# Search Apple Music for albums
result = await node.load_search(
    query="taylor swift",
    types=[lava_lyra.LavaSearchType.ALBUM],
    search_type=lava_lyra.SearchType.amsearch
)
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License and Credits

### License
This project is licensed under the **GPL-3.0 License** - see the [LICENSE](LICENSE) file for details.

### Credits and Attribution

**Lyra** is based on the excellent [**Pomice**](https://github.com/cloudwithax/pomice) library:

- **Original Pomice**: Copyright (c) 2023, [cloudwithax](https://github.com/cloudwithax)
- **Lyra (Lavalink v4 refactor)**: Copyright (c) 2025, ParrotXray

We extend our heartfelt thanks to **cloudwithax** and all Pomice contributors for creating the solid foundation that made Lyra possible. This project builds upon their excellent work to provide Lavalink v4 compatibility and modern server-side plugin support.

### Key Contributors
- **cloudwithax** - Original Pomice library creator
- **ParrotXray** - Lavalink v4 refactoring and Lyra development  
- **Community contributors** - Bug reports, features, and improvements

## Links

- [PyPI Package](https://pypi.org/project/lava-lyra/)
- [GitHub Repository](https://github.com/ParrotXray/Lyra)
- [Bug Reports](https://github.com/ParrotXray/lyra/issues)
- [Original Pomice](https://github.com/cloudwithax/pomice)

### Credits and Attribution

**Lyra** is based on the excellent [**Pomice**](https://github.com/cloudwithax/pomice) library:

- **Original Pomice**: Copyright (c) 2023, [cloudwithax](https://github.com/cloudwithax)
- **Lyra (Lavalink v4 refactor)**: Copyright (c) 2025, [ParrotXray](https://github.com/ParrotXray)

We extend our heartfelt thanks to **cloudwithax** and all Pomice contributors for creating the solid foundation that made Lyra possible. This project builds upon their excellent work to provide Lavalink v4 compatibility and modern server-side plugin support.

### Key Contributors
- **cloudwithax** - Original Pomice library creator
- **ParrotXray** - Lavalink v4 refactoring and Lyra development  
- **Community contributors** - Bug reports, features, and improvements

## Star History

If you find Lyra useful, please consider giving it a star!

---

*Made with love for the Discord music bot community*
