from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # discord.py
    from discord.ext.commands import Bot
    from discord.ext.commands import Context
    from discord.abc import Member, User, Guild
    # py-cord
    from discord import Bot
    from discord import ApplicationContext
    from discord import Member, User
    
class PackageRequirement:
    """
    Utilities for checking installed Discord libraries.

    This class provides static methods to detect whether
    `py-cord` or `discord.py` is installed in the environment.
    """

    @staticmethod
    def is_pycord() -> bool:
        """
        Check whether py-cord is installed.

        Returns:
            bool: True if py-cord is installed, otherwise False.
        """
        try:
            version("py-cord")
            return True
        except PackageNotFoundError:
            return False

    @staticmethod
    def is_discordpy() -> bool:
        """
        Check whether discord.py is installed.

        Returns:
            bool: True if discord.py is installed, otherwise False.
        """
        try:
            version("discord.py")
            return True
        except PackageNotFoundError:
            return False