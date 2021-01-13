"""
Provides several utilities
"""
import discord
from discord.ext import commands
from firebase_admin import firestore, credentials, initialize_app

from _util import checks, BLUE, set_db


class utils(commands.Cog):
    """
    Main class
    """
    def __init__(self, bot):
        self.bot = bot
        set_db(bot.db)

    @commands.command()
    @commands.check(checks.mod)
    async def slowmode(self, ctx, *, length):
        """
        Sets the slowmode of a channel
        """
        lens = length.split(" ")
        time = 0
        for period in lens:
            if period.endswith("s"):
                time += int(period[:-1])
            if period.endswith("m"):
                time += int(period[:-1])*60
            if period.endswith("h"):
                time += int(period[:-1])*60*60
        await ctx.message.delete()
        embed = discord.Embed(title=f"Slowmode set to {time} seconds({length})")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.channel.edit(slowmode_delay=time)
        await ctx.send(embed=embed)

    @commands.command()
    async def age(self, ctx, user: discord.Member):
        """
        Displays how long a member has had their discord account for and how long they have been in the server
        """
        embed = discord.Embed(title=user.display_name, description=f"**Created:** {user.created_at}\n**Joined:** {user.joined_at}", colour=BLUE)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(utils(bot))
