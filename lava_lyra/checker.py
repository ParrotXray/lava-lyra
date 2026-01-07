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

    BotType = "DiscordPyBot" | "PycordBot"
    ContextType = "DiscordPyContext" | "PycordContext"
    MemberType = "DiscordPyMember" | "PycordMember"
    UserType = "DiscordPyUser" | "PycordUser"
    GuildType = "DiscordPyGuild" | "PycordGuild"
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



def import_discord_types():
    if PackageRequirement.is_discordpy():
        from discord.ext.commands import Bot, Context
        from discord.abc import Member, User, Guild
        return Bot, Context, Member, User, Guild

    if PackageRequirement.is_pycord():
        from discord import Bot, ApplicationContext, Member, User, Guild
        return Bot, ApplicationContext, Member, User, Guild

    raise RequirementNotFound("Neither discord.py nor py-cord could be found")


Bot, Context, Member, User, Guild = import_discord_types()