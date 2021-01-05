"""
Allows users to link their discord to their minecraft account
"""
import requests

import discord
from discord.ext import commands
from firebase_admin import firestore, credentials, initialize_app

from core import trusted, BLUE, GREEN


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
        await self.bot.db.execute("UPDATE users SET mc_uuid = $2 WHERE id = $1", user.id, mc_account.json()["id"])
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
        if await self.bot.db.fetchval("SELECT mc_uuid FROM users WHERE id = $1", ctx.author.id) is None:
            await self.bot.db.execute("UPDATE users SET mc_uuid = $2 WHERE id = $1", ctx.author.id, mc_account.json()["id"])
            await ctx.message.delete()
            embed = discord.Embed(title="Link success", colour=GREEN)
            embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @commands.command()
    async def whois(self, ctx, user: discord.User):
        """
        Gets info about the mentioned user's minecraft account
        """
        uuid = await self.bot.db.fetchval("SELECT mc_uuid FROM users WHERE id = $1", user.id)
        if uuid is not None:
            name_history = requests.get(f"https://api.mojang.com/user/profiles/{uuid}/names")
            embed = discord.Embed(title=user.name, description=f"**Current name: **{name_history.json()[-1]['name']}", colour=BLUE)
            embed.set_thumbnail(url=f"https://crafatar.com/avatars/{uuid}")
            if uuid == "839a55edc0b5434581228b0c18874381":
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
        unlinked = await self.bot.db.fetch("SELECT id FROM users WHERE mc_uuid IS NULL")
        embed = discord.Embed(title="Unlinked users:", description="\n".join([f"<@{user['id']}>" for user in unlinked if not ctx.guild.get_member(user["id"]).bot]))
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(linking(bot))
