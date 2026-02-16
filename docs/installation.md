# Installation

This library is designed to work with the Lavalink v4 audio delivery system,
which directly interfaces with Discord to provide buttery smooth audio without
wasting your precious system resources.

Lyra is made with convenience in mind — everything is easy to use and out of
your way, while also being customizable.

## Setting up Lavalink

In order to start using this library, you need a running Lavalink v4 node.
You can download the latest release [here](https://github.com/lavalink-devs/Lavalink/releases/latest).

A minimal `application.yml` for Lavalink v4:

```yaml
server:
  port: 2333
  address: 0.0.0.0
lavalink:
  server:
    password: "youshallnotpass"
    sources:
      youtube: true
      soundcloud: true
```

For extended platform support (Spotify, Apple Music, Deezer, etc.) install the
[LavaSrc](https://github.com/topi314/LavaSrc) plugin on your Lavalink server.

## Installing Lyra

After your Lavalink node is up and running, install Lyra with pip:

```
pip install lava-lyra
```

Lyra will handle installing all required dependencies automatically.

## Next Steps

After installing Lyra, get familiar with how it works by starting with [an example.](quickstart.md)

If you want to jump into the library and learn how to do everything you need,
refer to the [How Do I?](hdi/index.md) section.

If you want a deeper look into how the library works beyond the [How Do I?](hdi/index.md)
guide, refer to the [API Reference](api/index.md) section.
