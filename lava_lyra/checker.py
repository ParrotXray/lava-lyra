# type: ignore
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING
from .exceptions import RequirementNotFound


if TYPE_CHECKING:
    # discord.py
    from discord.ext.commands import Bot as DiscordPyBot
    from discord.ext.commands import Context as DiscordPyContext
    from discord.abc import Member as DiscordPyMember, User as DiscordPyUser, Guild as DiscordPyGuild

    # py-cord
    from discord import Bot as PycordBot
    from discord import ApplicationContext as PycordContext
    from discord import Member as PycordMember, User as PycordUser, Guild as PycordGuild

    # disnake
    from disnake.ext.commands import Bot as DisnakeBot
    from disnake.ext.commands import Context as DisnakeContext
    from disnake import Member as DisnakeMember, User as DisnakeUser, Guild as DisnakeGuild

    # nextcord
    from nextcord.ext.commands import Bot as NextBot
    from nextcord.ext.commands import Context as NextContext
    from nextcord import Member as NextMember, User as NextUser, Guild as NextGuild

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
            from discord.ext.commands import Bot, Context
            from discord import Member, User, Guild
            from discord import VoiceChannel, VoiceProtocol, ClientUser
            return Bot, Context, Member, User, Guild, VoiceChannel, VoiceProtocol, ClientUser
        except:
            raise ImportError("discord.py>=2.0 is required")

    elif PackageRequirement.is_pycord():
        try:
            from discord import Bot, ApplicationContext, Member, User, Guild, VoiceChannel, VoiceProtocol, ClientUser
            return Bot, ApplicationContext, Member, User, Guild, VoiceChannel, VoiceProtocol, ClientUser
        except:
            raise ImportError("py-cord>=2.0 is required")

    elif PackageRequirement.is_disnake():
        try:
            from disnake.ext.commands import Bot, Context
            from disnake import Member, User, Guild, VoiceChannel, VoiceProtocol, ClientUser
            return Bot, Context, Member, User, Guild, VoiceChannel, VoiceProtocol, ClientUser
        except:
            raise ImportError("disnake>=2.0 is required")

    elif PackageRequirement.is_nextcord():
        try:
            from nextcord.ext.commands import Bot, Context
            from nextcord import Member, User, Guild, VoiceChannel, VoiceProtocol, ClientUser
            return Bot, Context, Member, User, Guild, VoiceChannel, VoiceProtocol, ClientUser
        except:
            raise ImportError("nextcord>=2.5 is required")

    raise RequirementNotFound("Neither discord.py, py-cord, disnake, nor nextcord could be found")


Bot, ApplicationContext, Member, User, Guild, VoiceChannel, VoiceProtocol, ClientUser = import_discord_types()
