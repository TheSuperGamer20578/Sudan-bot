"""
Setup moderation stuff
THIS IS STILL A WORK IN PROGRESS
"""
import discord
from discord.ext import commands
from firebase_admin import firestore, credentials, initialize_app
from core import admin

try:
    cred = credentials.Certificate("Config/firebase.json")
    initialize_app(cred)
except ValueError:
    pass
db = firestore.client()
fs_data = db.collection("settings")


class moderation_config(commands.Cog):
    """
    Main class
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(admin)
    async def mutesetup(self, ctx):
        """
        Set overrides for mute role
        """
        mute = ctx.guild.get_role(int(fs_data.document(str(ctx.guild.id)).get().to_dict()["muterole"]))
        for x in ctx.guild.channels:
            x.edit(overwrites={mute: discord.PermissionOverwrite(send_messages=False)})
            x.edit(overwrites={mute: discord.PermissionOverwrite(speak=False)})
        await ctx.message.delete()
        embed = discord.Embed(title="mute role overrides set")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(moderation_config(bot))
