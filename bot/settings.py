"""
A global config for the bot
"""
import re

import discord
from discord.ext import commands

from _util import GREEN

settable = {
    "mod_roles": list,
    "admin_roles": list,
    "support_role": int,
    "chain_break_role": int
}


class settings(commands.Cog):
    """
    Main class
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_guild_permissions(manage_guild=True)
    async def set(self, ctx, thing, value):
        """
        Changes settings
        """
        match = re.match("^<[@#][!&]?([0-9]{17,18})>$", value)
        if match:
            value = match.group(1)
        if thing not in settable:
            raise commands.errors.BadArgument()
        if settable[thing] == list:
            value = [value]
        await self.bot.db.execute("UPDATE guilds SET $2 = $3 WHERE id = $1", ctx.guild.id, thing, settable[thing](value))
        await ctx.message.delete()
        embed = discord.Embed(title="Settings updated", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(settings(bot))
