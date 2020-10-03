import discord
from discord.ext import commands
from core import admin
import firebase_admin
from firebase_admin import *
from firebase_admin import firestore

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase.json")
    initialize_app(cred)
db = firestore.client()
fs_data = db.collection("settings")


class moderation_config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(admin)
    async def mutesetup(self, ctx):
        mute = ctx.guild.get_role(int(fs_data.document(str(ctx.guild.id)).get().to_dict()["muterole"]))
        for x in ctx.guild.channels:
            x.edit(overwrites={mute: discord.PermissionOverwrite(send_messages=False)})
            x.edit(overwrites={mute: discord.PermissionOverwrite(speak=False)})
        await ctx.message.delete()
        embed = discord.Embed(title="mute role overrides set")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(moderation_config(bot))
