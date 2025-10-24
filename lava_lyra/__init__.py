"""
Lyra
~~~~
A modern Lavalink v4 wrapper designed for py-cord.
Based on the original Pomice library by cloudwithax.

This version has been completely refactored to work with Lavalink v4,
removing client-side parsing in favor of server-side plugins.

Key improvements in Lyra:
- Full Lavalink v4 REST API support
- Server-side plugin integration (LavaSrc, YouTube plugin, etc.)
- Simplified node creation (no more API credentials needed)
- Better error handling and plugin support
- Removed deprecated client-side parsing modules

Platform support (Spotify, Apple Music, Bilibili, etc.) is now handled
entirely by Lavalink server plugins. Configure these in your Lavalink
server's application.yml file instead of the client.

Original Pomice Copyright (c) 2023, cloudwithax
Lavalink v4 refactoring Copyright (c) 2025, ParrotXray

Licensed under GPL-3.0
"""

from typing import NamedTuple

import discord

if not discord.version_info.major >= 2:

    class DiscordPyOutdated(Exception):
        pass

    raise DiscordPyOutdated(
        "You must have py-cord (v2.0 or greater) to use this library. "
        "Uninstall your current version and install py-cord 2.0 "
        "using 'pip install py-cord'",
    )


class _VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    release: str
    serial: int


__version__ = "1.4.0"
__version_info__ = _VersionInfo(1, 4, 0, "final", 0)

version = __version__
version_info = __version_info__
__title__ = "lava_lyra"
__author__ = "ParrotXray"
__license__ = "GPL-3.0"
__copyright__ = "Copyright (c) 2025, ParrotXray. Based on Pomice by cloudwithax"

from .enums import *
from .events import *
from .exceptions import *
from .filters import *
from .lyrics import *
from .objects import *
from .player import *
from .pool import *
from .routeplanner import *
from .trackqueue import *
