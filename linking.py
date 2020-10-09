"""
Allows users to link their discord to their minecraft account
"""
import requests

import discord
from discord.ext import commands
from firebase_admin import firestore, credentials, initialize_app

from core import trusted, BLUE, GREEN

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
        mc_account = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{mcname}")
        if mc_account.status_code != 200:
            return
        fs_data.document(str(user.id)).set({"mcname": mc_account.json()["name"]})
        await ctx.message.delete()
        embed = discord.Embed(title="Link success", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def linkme(self, ctx, mcname):
        """
        Link to your minecraft account
        """
        mc_account = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{mcname}")
        if mc_account.status_code != 200:
            return
        if not fs_data.document(str(ctx.author.id)).get().to_dict():
            fs_data.document(str(ctx.author.id)).set({"mcname": mc_account.json()["name"]})
            await ctx.message.delete()
            embed = discord.Embed(title="Link success", colour=GREEN)
            embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @commands.command()
    async def whois(self, ctx, user: discord.User):
        """
        Gets info about the mentioned user's minecraft account
        """
        data = fs_data.document(str(user.id)).get().to_dict()
        if data:
            mc_account = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{data['mcname']}")
            if mc_account.status_code != 200:
                return
            uuid = mc_account.json()["id"]
            name_history = requests.get(f"https://api.mojang.com/user/profiles/{uuid}/names")
            embed = discord.Embed(title=user.name, description=f"**Current name: **{data['mcname']}", colour=BLUE)
            embed.set_thumbnail(url=f"https://crafatar.com/avatars/{uuid}")
            if data["mcname"] == "TheSuperGamer205":
                embed.add_field(name="Name history", value="TheSuperGamer205")
            else:
                embed.add_field(name="Name history", value="\n".join([history["name"] for history in name_history.json()]))
        else:
            embed = discord.Embed(title=user.name, description="That user hasn't linked there mc account yet!", colour=BLUE)
        await ctx.message.delete()
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def unlinked(self, ctx):
        """
        Displays a list of all unlinked users in this server
        """
        msg = ""
        for member in ctx.guild.members:
            if member.bot:
                continue
            data = fs_data.document(str(member.id)).get().to_dict()
            if data is None:
                msg += f"{member.mention}\n"
        embed = discord.Embed(title="Unlinked users:", description=msg)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(linking(bot))
