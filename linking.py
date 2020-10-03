import discord
from discord.ext import commands
import firebase_admin
import requests
# import base64
# import json
from firebase_admin import *
from firebase_admin import firestore
from core import trusted, blue, green

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase.json")
    initialize_app(cred)
db = firestore.client()
fs_data = db.collection("linking")


class linking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(trusted)
    async def link(self, ctx, user: discord.User, mcname):
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
    bot.add_cog(linking(bot))
