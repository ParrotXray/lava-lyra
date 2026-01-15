"""
Compatibility layer for py-cord, discord.py, disnake, and nextcord
"""

from __future__ import annotations
from importlib.metadata import PackageNotFoundError, version


# Try to import Discord library

try:
    import discord
except ImportError:
    try:
        import disnake as discord
    except ImportError:
        try:
            import nextcord as discord
        except ImportError:
            raise ImportError(
                "You must have one of py-cord, discord.py, disnake, or nextcord installed."
            )


# Detect which library is being used

IS_PYCORD = IS_DPY = IS_DISNAKE = IS_NEXTCORD = False

try:
    version("py-cord")
    IS_PYCORD = True
except PackageNotFoundError:
    try:
        version("discord.py")
        IS_DPY = True
    except PackageNotFoundError:
        try:
            version("disnake")
            IS_DISNAKE = True
        except PackageNotFoundError:
            try:
                version("nextcord")
                IS_NEXTCORD = True
            except PackageNotFoundError:
                raise ImportError(
                    "You must have one of py-cord, discord.py, disnake, or nextcord installed."
                )


# Type aliases

from discord import ClientUser as ClientUserType
from discord import Guild as GuildType
from discord import Interaction as InteractionType
from discord import Member as MemberType
from discord import User as UserType
from discord import VoiceChannel as VoiceChannelType
from discord import VoiceProtocol as VoiceProtocolType

if IS_PYCORD or IS_DISNAKE or IS_NEXTCORD:
    from discord import ApplicationContext as ContextType
    from discord import Bot as BotType
elif IS_DPY:
    from discord.ext.commands import Bot as BotType
    from discord.ext.commands import Context as ContextType


# Public API

__all__ = (
    "IS_PYCORD",
    "IS_DPY",
    "IS_DISNAKE",
    "IS_NEXTCORD",
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
