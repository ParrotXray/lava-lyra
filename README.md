# Lyra

[![PyPI](https://img.shields.io/pypi/v/lava-lyra.svg)](https://pypi.org/project/lava-lyra/)
[![Python](https://img.shields.io/pypi/pyversions/lava-lyra.svg)](https://pypi.org/project/lava-lyra/)
[![License](https://img.shields.io/github/license/ParrotXray/lava-lyra.svg)](https://github.com/ParrotXray/Lyra/blob/main/LICENSE)

A modern Lavalink v4 wrapper designed for py-cord, based on the excellent [Pomice](https://github.com/cloudwithax/pomice) library by cloudwithax.

## What's New in Lyra

Lyra is a complete refactor of Pomice for **Lavalink v4**, bringing significant improvements:

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
        nodes = await lava_lyra.NodePool.create_nodes(
          self, 
          host='http://localhost:2333', 
          port=3030, 
          password='youshallnotpass', 
          identifier='MAIN', 
          lyrics=False, 
          fallback=True
        )
        print(f"Created {len(nodes)} nodes")

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
