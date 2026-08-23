"""
Compatibility layer for py-cord and discord.py
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Any

# Try to import discord library
try:
    import discord  # noqa: F401
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
from discord import Member as MemberType
from discord import StageChannel as StageChannelType
from discord import User as UserType
from discord import VoiceChannel as VoiceChannelType
from discord import VoiceProtocol as VoiceProtocolType

VoiceChannelTypes: tuple[type[VoiceChannelType], type[StageChannelType]] = (
    VoiceChannelType,
    StageChannelType,
)

if IS_PYCORD:
    from discord import ApplicationContext as ContextType  # pyrefly: ignore
    from discord import Bot as BotType  # pyrefly: ignore
    from discord.raw_models import (
        RawVoiceServerUpdateEvent as VoiceServerUpdateType,  # pyrefly: ignore
    )
    from discord.raw_models import (
        RawVoiceStateUpdateEvent as GuildVoiceStateType,  # pyrefly: ignore
    )
elif IS_DPY:
    from discord.ext.commands import Bot as BotType
    from discord.ext.commands import Context as _Context
    from discord.types.voice import GuildVoiceState as GuildVoiceStateType
    from discord.types.voice import VoiceServerUpdate as VoiceServerUpdateType

    type ContextType = _Context[Any]

__all__ = (
    "IS_DPY",
    "IS_PYCORD",
    "BotType",
    "ClientUserType",
    "ContextType",
    "GuildType",
    "GuildVoiceStateType",
    "MemberType",
    "StageChannelType",
    "UserType",
    "VoiceChannelType",
    "VoiceChannelTypes",
    "VoiceProtocolType",
    "VoiceServerUpdateType",
)
