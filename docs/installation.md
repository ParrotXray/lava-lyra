# Installation

This library is designed to work with the Lavalink v4 (or NodeLink v3) audio delivery system,
which directly interfaces with Discord to provide buttery smooth audio without
wasting your precious system resources.

Lyra is made with convenience in mind — everything is easy to use and out of
your way, while also being customizable.

## Setting up Lavalink or NodeLink

In order to start using this library, you need a running Lavalink v4 node, or a
[NodeLink v3](https://github.com/PerformanC/NodeLink) instance instead.
You can download the latest Lavalink release [here](https://github.com/lavalink-devs/Lavalink/releases/latest).

A minimal `application.yml` for Lavalink v4:

```yaml
server:
  port: 2333
  address: 127.0.0.1

lavalink:
  plugins:
    # Required for YouTube support
    - dependency: "dev.lavalink.youtube:youtube-plugin:VERSION"
      repository: "https://maven.lavalink.dev/releases"

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
      clientId: ""
      clientSecret: ""
      spDc: ""
      countryCode: "US"
      customTokenEndpoint: "http://localhost:8080/api/token"

    applemusic:
      countryCode: "US"

      # The following settings, manually input or empty to get a token automatically
      mediaAPIToken: "your apple music api token" # apple music api token
      # or specify an apple music key
      keyID: "your key id"
      teamID: "your team id"
      musicKitKey: |
        -----BEGIN PRIVATE KEY-----
        your key
        -----END PRIVATE KEY-----
```

For extended platform support (Spotify, Apple Music, Deezer, etc.) install the
[LavaSrc](https://github.com/topi314/LavaSrc) plugin on your Lavalink server.

Alternatively, the minimal `server` block of a [NodeLink v3](https://github.com/PerformanC/NodeLink)
`config.default.ts` you'll need to point Lyra at looks like this:

```ts
import type { NodelinkConfig } from './src/typings/config/config.types.ts'

export const config: NodelinkConfig = {
  server: {
    host: '0.0.0.0',
    port: 3000,
    password: 'youshallnotpass',
    useBunServer: false
  },
  // ...rest of the config controls clustering, logging, sources, etc.
}

export default config
```

The `host`/`port`/`password` values here map directly to the `host`, `port`, and `password`
arguments you'll pass to `NodePool.create_node()`.

## Installing Lyra

After your Lavalink or NodeLink instance is up and running, install Lyra with pip:

```
pip install lava-lyra
```

Lyra doesn't bundle a Discord library by default — install it as an extra alongside Lyra,
depending on which one you use:

```
pip install lava-lyra[py-cord]
# or
pip install lava-lyra[discord.py]
```

For better performance under load, you can also install the `speed` extra, which pulls in
`aiohttp[speedups]`, `aiodns`, and `orjson`:

```
pip install lava-lyra[speed]
```

## Next Steps

After installing Lyra, get familiar with how it works by starting with [an example.](quickstart.md)
