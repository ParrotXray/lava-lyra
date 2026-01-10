# type: ignore
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

from .exceptions import RequirementNotFound

if TYPE_CHECKING:
    # discord.py
    # py-cord
    from discord import ApplicationContext as PycordContext
    from discord import Bot as PycordBot
    from discord import Guild as PycordGuild
    from discord import Member as PycordMember
    from discord import User as PycordUser
    from discord.abc import Guild as DiscordPyGuild
    from discord.abc import Member as DiscordPyMember
    from discord.abc import User as DiscordPyUser
    from discord.ext.commands import Bot as DiscordPyBot
    from discord.ext.commands import Context as DiscordPyContext
    from disnake import Guild as DisnakeGuild
    from disnake import Member as DisnakeMember
    from disnake import User as DisnakeUser

    # disnake
    from disnake.ext.commands import Bot as DisnakeBot
    from disnake.ext.commands import Context as DisnakeContext
    from nextcord import Guild as NextGuild
    from nextcord import Member as NextMember
    from nextcord import User as NextUser

    # nextcord
    from nextcord.ext.commands import Bot as NextBot
    from nextcord.ext.commands import Context as NextContext

    BotType = "DiscordPyBot" | "PycordBot" | "DisnakeBot" | "NextBot"
    ContextType = "DiscordPyContext" | "PycordContext" | "DisnakeContext" | "NextContext"
    MemberType = "DiscordPyMember" | "PycordMember" | "DisnakeMember" | "NextMember"
    UserType = "DiscordPyUser" | "PycordUser" | "DisnakeUser" | "NextUser"
    GuildType = "DiscordPyGuild" | "PycordGuild" | "DisnakeGuild" | "NextGuild"
    ClientUserType = BotType


class PackageRequirement:
    """Check if py-cord or discord.py is installed."""

    @staticmethod
    def is_pycord() -> bool:
        try:
            version("py-cord")
            return True
        except PackageNotFoundError:
            return False

    @staticmethod
    def is_discordpy() -> bool:
        try:
            version("discord.py")
            return True
        except PackageNotFoundError:
            return False

    @staticmethod
    def is_disnake() -> bool:
        try:
            version("disnake")
            return True
        except PackageNotFoundError:
            return False

    @staticmethod
    def is_nextcord() -> bool:
        try:
            version("nextcord")
            return True
        except PackageNotFoundError:
            return False


def import_discord_types() -> tuple:
    if PackageRequirement.is_discordpy():
        try:
            from discord import ClientUser, Guild, Member, User, VoiceChannel, VoiceProtocol
            from discord.ext.commands import Bot, Context

            return Bot, Context, Member, User, Guild, VoiceChannel, VoiceProtocol, ClientUser
        except:
            raise ImportError("discord.py>=2.0 is required")

    elif PackageRequirement.is_pycord():
        try:
            from discord import (
                ApplicationContext,
                Bot,
                ClientUser,
                Guild,
                Member,
                User,
                VoiceChannel,
                VoiceProtocol,
            )

            return (
                Bot,
                ApplicationContext,
                Member,
                User,
                Guild,
                VoiceChannel,
                VoiceProtocol,
                ClientUser,
            )
        except:
            raise ImportError("py-cord>=2.0 is required")

    elif PackageRequirement.is_disnake():
        try:
            from disnake import ClientUser, Guild, Member, User, VoiceChannel, VoiceProtocol
            from disnake.ext.commands import Bot, Context

            return Bot, Context, Member, User, Guild, VoiceChannel, VoiceProtocol, ClientUser
        except:
            raise ImportError("disnake>=2.0 is required")

    elif PackageRequirement.is_nextcord():
        try:
            from nextcord import ClientUser, Guild, Member, User, VoiceChannel, VoiceProtocol
            from nextcord.ext.commands import Bot, Context

            return Bot, Context, Member, User, Guild, VoiceChannel, VoiceProtocol, ClientUser
        except:
            raise ImportError("nextcord>=2.5 is required")

    raise RequirementNotFound("Neither discord.py, py-cord, disnake, nor nextcord could be found")


Bot, ApplicationContext, Member, User, Guild, VoiceChannel, VoiceProtocol, ClientUser = (
    import_discord_types()
)
