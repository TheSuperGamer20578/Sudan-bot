"""
Provides several utilities
"""
import discord
from discord.ext import commands
from firebase_admin import *
from firebase_admin import firestore
from .core import mod, admin, blue

try:
    cred = credentials.Certificate("Config/firebase.json")
    initialize_app(cred)
except ValueError:
    pass
db = firestore.client()
fs_data = db.collection("utils")


class utils(commands.Cog):
    """
    Main class
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Delete message if its blank
        """
        if (len(message.content.replace(" ", "").replace("*", "").replace("_", "")) <= 0) and not (
                message.author.bot or len(message.attachments) or message.is_system())\
                and str(message.guild.id) in fs_data.document("no-blank").get().to_dict()["servers"]:
            await message.delete()

    @commands.command()
    @commands.check(admin)
    async def noblank(self, ctx):
        """
        Makes the bot delete blank messages
        """
        await ctx.message.delete()
        if ctx.guild.id in fs_data.document("no-blank").get().to_dict()["servers"]:
            embed = discord.Embed(title="Blank messages will no longer be deleted")
            fs_data.document("no-blank").set(
                {"servers": [x for x in fs_data.document("no-blank").get().to_dict()["servers"] if x != str(ctx.guild.id)]})
        else:
            embed = discord.Embed(title="Blank messages will now be deleted")
            d = fs_data.document("no-blank").get().to_dict()["servers"]
            d.append(str(ctx.guild.id))
            fs_data.document("no-blank").set({"servers": d})
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.check(mod)
    async def slowmode(self, ctx, *, length):
        """
        Sets the slowmode of a channel
        """
        t = length.split(" ")
        time = 0
        for x in t:
            if x.endswith("s"):
                time += int(x[:-1])
            if x.endswith("m"):
                time += int(x[:-1])*60
            if x.endswith("h"):
                time += int(x[:-1])*60*60
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
        embed = discord.Embed(title=user.display_name, description=f"**Created:** {user.created_at}\n**Joined:** {user.joined_at}", colour=blue)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(utils(bot))
