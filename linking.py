"""
Allows users to link their discord to their minecraft account
"""
import discord
from discord.ext import commands
import requests
from firebase_admin import *
from firebase_admin import firestore
from .core import trusted, blue, green

try:
    cred = credentials.Certificate("Config/firebase.json")
    initialize_app(cred)
except ValueError:
    pass
db = firestore.client()
fs_data = db.collection("linking")


class linking(commands.Cog):
    """
    Main class
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(trusted)
    async def link(self, ctx, user: discord.User, mcname):
        """
        Links a user to their minecraft account
        """
        mc = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{mcname}")
        if mc.status_code != 200:
            return
        fs_data.document(str(user.id)).set({"mcname": mc.json()["name"]})
        await ctx.message.delete()
        embed = discord.Embed(title="Link success", colour=green)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def linkme(self, ctx, mcname):
        """
        Link to your minecraft account
        """
        mc = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{mcname}")
        if mc.status_code != 200:
            return
        if not fs_data.document(str(ctx.author.id)).get().to_dict():
            fs_data.document(str(ctx.author.id)).set({"mcname": mc.json()["name"]})
            await ctx.message.delete()
            embed = discord.Embed(title="Link success", colour=green)
            embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @commands.command()
    async def whois(self, ctx, user: discord.User):
        """
        Gets info about the mentioned user's minecraft account
        """
        d = fs_data.document(str(user.id)).get().to_dict()
        if d:
            mc = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{d['mcname']}")
            if mc.status_code != 200:
                return
            id = mc.json()["id"]
            name_history = requests.get(f"https://api.mojang.com/user/profiles/{id}/names")
            embed = discord.Embed(title=user.name, description=f"**Current name: **{d['mcname']}", colour=blue)
            embed.set_thumbnail(url=f"https://crafatar.com/avatars/{id}")
            if d["mcname"] == "TheSuperGamer205":
                embed.add_field(name="Name history", value="TheSuperGamer205")
            else:
                embed.add_field(name="Name history", value="\n".join([x["name"] for x in name_history.json()]))
        else:
            embed = discord.Embed(title=user.name, description="That user hasn't linked there mc account yet!", colour=blue)
        await ctx.message.delete()
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def unlinked(self, ctx):
        """
        Displays a list of all unlinked users in this server
        """
        msg = ""
        for x in ctx.guild.members:
            if x.bot:
                continue
            d = fs_data.document(str(x.id)).get().to_dict()
            if d is None:
                msg += f"{x.mention}\n"
        embed = discord.Embed(title="Unlinked users:", description=msg)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(linking(bot))
