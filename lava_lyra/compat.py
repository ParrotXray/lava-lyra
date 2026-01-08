"""
Compatibility layer for py-cord and discord.py
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

# Try to import discord library
try:
    import discord
except ImportError:
    raise ImportError("You must have either py-cord or discord.py installed to use this library.")

# Detect which library is being used
try:
    version("py-cord")
    IS_PYCORD = True
    IS_DPY = False
except PackageNotFoundError:
    try:
        version("discord.py")
        IS_PYCORD = False
        IS_DPY = True
    except PackageNotFoundError:
        raise ImportError(
            "You must have either py-cord or discord.py installed to use this library."
        )

from discord import ClientUser as ClientUserType
from discord import Guild as GuildType
from discord import Interaction as InteractionType
from discord import Member as MemberType
from discord import User as UserType
from discord import VoiceChannel as VoiceChannelType
from discord import VoiceProtocol as VoiceProtocolType

if IS_PYCORD:
    from discord import ApplicationContext as ContextType
    from discord import Bot as BotType
elif IS_DPY:
    from discord.ext.commands import Bot as BotType
    from discord.ext.commands import Context as ContextType

__all__ = (
    "IS_PYCORD",
    "ContextType",
    "InteractionType",
    "BotType",
    "MemberType",
    "ClientUserType",
    "UserType",
    "VoiceChannelType",
    "VoiceProtocolType",
    "GuildType",
)
