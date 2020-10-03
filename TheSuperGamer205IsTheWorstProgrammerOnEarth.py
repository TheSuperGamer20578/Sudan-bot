import discord
from discord.ext import commands


class TheSuperGamer205IsTheWorstProgrammerOnEarth(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def TheSuperGamer205IsTheWorstProgrammerOnEarth(self, ctx):
        await ctx.send("😳")


def setup(bot):
    bot.add_cog(TheSuperGamer205IsTheWorstProgrammerOnEarth(bot))
