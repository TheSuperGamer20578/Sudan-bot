import discord
import re
from discord.ext import commands
import firebase_admin
from firebase_admin import *
from firebase_admin import firestore
from core import green

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase.json")
    initialize_app(cred)
db = firestore.client()
fs_data = db.collection("settings")

settable = ["modrole", "adminrole", "muterole", "breakrole"]


class settings(commands.Cog):
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
        m = re.match("^<[@#][!&]?([0-9]{17,18})>$", value)
        if m:
            value = m.group(1)
        if thing not in settable:
            raise commands.errors.BadArgument()
        d = fs_data.document(str(ctx.guild.id)).get().to_dict()
        if d is None:
            d = {}
        d[thing] = value
        fs_data.document(str(ctx.guild.id)).set(d)
        await ctx.message.delete()
        embed = discord.Embed(title="Settings updated", colour=green)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(settings(bot))
