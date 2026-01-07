from importlib.metadata import PackageNotFoundError, version

class PackageRequirement():
    """Function for checking requirement(discord.py or pycord)
    Return the function checker is_{package} -> bool"""
    
    @staticmethod
    def is_pycord():
        """Function for checking whether pycord installed
        Return the function checker is_pycord() -> bool"""
        try:
            version("py-cord")
            return True
        except PackageNotFoundError:
            pass

        return False
        
    @staticmethod
    def is_discordpy():
        """Function for checking whether discord.py installed
        Return the function checker is_discordpy() -> bool"""
        try:
            version("discord.py")
            return True
        except PackageNotFoundError:
            pass

        return False