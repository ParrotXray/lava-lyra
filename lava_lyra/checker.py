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

    BotType = "DiscordPyBot" | "PycordBot" | "DisnakeBot"
    ContextType = "DiscordPyContext" | "PycordContext" | "DisnakeContext"
    MemberType = "DiscordPyMember" | "PycordMember" | "DisnakeMember"
    UserType = "DiscordPyUser" | "PycordUser" | "DisnakeUser
    GuildType = "DiscordPyGuild" | "PycordGuild" | "DisnakeGuild"
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


def import_discord_types():
    if PackageRequirement.is_discordpy():
        from discord.ext.commands import Bot, Context
        from discord import Member, User, Guild
        from discord import VoiceChannel, VoiceProtocol, ClientUser
        return Bot, Context, Member, User, Guild, VoiceChannel, VoiceProtocol, ClientUser

    elif PackageRequirement.is_pycord():
        from discord import Bot, ApplicationContext, Member, User, Guild, VoiceChannel, VoiceProtocol, ClientUser
        return Bot, ApplicationContext, Member, User, Guild, VoiceChannel, VoiceProtocol, ClientUser

    elif PackageRequirement.is_disnake():
        from disnake.ext.commands import Bot, Context
        from disnake import Member, User, Guild, VoiceChannel, VoiceProtocol, ClientUser
        return Bot, Context, Member, User, Guild, VoiceChannel, VoiceProtocol, ClientUser

    raise RequirementNotFound("Neither discord.py, py-cord nor disnake could be found")


Bot, ApplicationContext, Member, User, Guild, VoiceChannel, VoiceProtocol, ClientUser = import_discord_types()
