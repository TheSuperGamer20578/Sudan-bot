"""
Requested by ogx#2920 i think it was to test how fast i could add stuff but idk
"""
from discord.ext import commands


class TheSuperGamer205IsTheWorstProgrammerOnEarth(commands.Cog):
    """
    Requested by ogx#2920
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def TheSuperGamer205IsTheWorstProgrammerOnEarth(self, ctx):
        """
        Send that emoji dont ask me why
        """
        await ctx.send("😳")


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(TheSuperGamer205IsTheWorstProgrammerOnEarth(bot))
