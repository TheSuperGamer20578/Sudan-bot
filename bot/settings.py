"""
A global config for the bot
"""
import re

import discord
from discord.ext import commands
from firebase_admin import firestore, credentials, initialize_app

from _util import GREEN

try:
    cred = credentials.Certificate("firebase.json")
    initialize_app(cred)
except ValueError:
    pass
db = firestore.client()
fs_data = db.collection("settings")

settable = ["modrole", "adminrole", "muterole", "breakrole"]


class settings(commands.Cog):
    """
    Main class
    """
    def __init__(self, bot):
        self.bot = bot

    # @commands.command()
    # async def setup(self, ctx, thing):
    #     pass

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
        data = fs_data.document(str(ctx.guild.id)).get().to_dict()
        if data is None:
            data = {}
        data[thing] = value
        fs_data.document(str(ctx.guild.id)).set(data)
        await ctx.message.delete()
        embed = discord.Embed(title="Settings updated", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(settings(bot))
