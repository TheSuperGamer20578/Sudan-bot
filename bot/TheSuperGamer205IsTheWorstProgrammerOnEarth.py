"""
Requested by ogx#2920 I think it was to test how fast I could add stuff but idk
"""
from discord.ext import commands


class TheSuperGamer205IsTheWorstProgrammerOnEarth(commands.Cog):
    """
    Requested by ogx#2920
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def thesupergamer205istheworstprogrammeronearth(self, ctx):
        """
        Send that emoji don't ask me why
        """
        await ctx.send("😳")


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(TheSuperGamer205IsTheWorstProgrammerOnEarth(bot))
