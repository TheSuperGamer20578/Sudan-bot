"""
Contains fun stuff
"""
import re
from os import getenv

import discord
from discord.ext import commands

from _Util import Checks, GREEN, RED


async def check_no_chain_forever(ctx):
    """Check that chainforever is not active"""
    async with ctx.bot.pool.acquire() as db:
        return await db.fetchval("SELECT chain_forever FROM channels WHERE id = $1", ctx.channel.id) is None


class Fun(commands.Cog):
    """
    The main class for this file
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def lmgtfy(self, ctx, *, query):
        """
        When someone bothers you with their questions use this command to link them to google after they have a little laugh
        """
        await ctx.message.delete()
        embed = discord.Embed(title=query,
                              url=f"https://lmgtfy.com/?q={query.replace(' ', '%20')}&pp=1&iie=1")
        embed.set_author(name=ctx.author.nick, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.check(
        lambda ctx: "sudont" not in [role.name for role in ctx.author.roles])
    async def sudo(self, ctx, user: discord.Member, *, message):
        """
        Mimics another user
        """
        await ctx.message.delete()
        webhook = await ctx.channel.create_webhook(
            name=user.nick if user.nick is not None else user.name)
        await webhook.send(message,
                           avatar_url=user.avatar_url)
        await webhook.delete()

    @commands.check(check_no_chain_forever)
    @commands.command()
    async def chain(self, ctx, *, thing):
        """
        Starts a chain
        """
        if thing.startswith("$counting:"):
            if thing.split(":", 1)[1] == "" or any(char not in "0123456789" for char in thing.split(":", 1)[1]) or thing.split(":", 1)[1][0] == "0":
                raise commands.BadArgument
            await ctx.send(f"Counting started at: {thing.split(':', 1)[1]}")
        else:
            await ctx.send(f"New chain: {thing}")
        await self.bot.db.execute("UPDATE channels SET last_chain = NULL, chain = $2 WHERE id = $1", ctx.channel.id, thing)

    @commands.check(Checks.admin)
    @commands.command()
    async def chainforever(self, ctx, *, thing=None):
        """Starts a chain that restarts when broken"""
        await ctx.message.delete()
        if thing is None:
            embed = discord.Embed(title="Chain disabled", colour=RED)
        else:
            if thing.startswith("$counting:"):
                if thing.split(":", 1)[1] == "" or any(char not in "0123456789" for char in thing.split(":", 1)[1]) or thing.split(":", 1)[1][0] == "0":
                    raise commands.BadArgument
            embed = discord.Embed(title="Chain updated", description=f"New chain: {thing}", colour=GREEN)
        await self.bot.db.execute("UPDATE channels SET last_chain = NULL, chain_forever = $2, chain = $2 WHERE id = $1", ctx.channel.id, thing)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    async def chain_check(self, msg):
        """
        Checks to see if chain is broken
        """
        if isinstance(msg.channel, discord.DMChannel):
            return
        bot = self.bot
        async with self.bot.pool.acquire() as db:
            chain_ = await db.fetchrow("SELECT chain, chain_length, chain_forever FROM channels WHERE id = $1", msg.channel.id)
            chain = chain_["chain"]
            length = chain_["chain_length"]
            forever = chain_["chain_forever"]

            async def cbreak():
                """
                If the chain is broken say so and update DB
                """
                if forever is not None:
                    if any(msg.content.startswith(f"{prefix}chainforever") for prefix in getenv("PREFIXES").split(",")) and await Checks.admin(msg, bot):
                        return
                    embed = discord.Embed(title="Chain broken!", description=f"{msg.author.mention} broke the chain!", colour=RED)
                    embed.add_field(name="Length", value=length)
                    embed.set_author(name=msg.author.display_name, icon_url=msg.author.avatar_url)
                    message = await msg.reply(embed=embed)
                    if length >= int(getenv("CHAIN_PIN_THRESHOLD")):
                        await message.pin()
                else:
                    await msg.channel.send(f"{msg.author.mention} broke the chain! start a new chain with `.chain <thing>`. Chain length: {length}")
                await msg.add_reaction("❌")
                break_role = await db.fetchval("SELECT chain_break_role FROM guilds WHERE id = $1", msg.guild.id)
                if break_role is not None:
                    await msg.author.add_roles(msg.guild.get_role(break_role))
                await db.execute("UPDATE channels SET chain = $2, chain_length = 0, last_chain = NULL WHERE id = $1", msg.channel.id, forever)

            if chain is None or msg.author.bot:
                return
            if chain.startswith("$counting:"):
                num = int(chain.split(":")[1])
                if msg.content != str(num):
                    return await cbreak()
                num += 1
                chain = f"$counting:{num}"
                await db.execute("UPDATE channels SET chain = $2 WHERE id = $1", msg.channel.id, chain)
            elif msg.content != chain:
                return await cbreak()
            if msg.author.id == await db.fetchval("SELECT last_chain FROM channels WHERE id = $1", msg.channel.id):
                return await cbreak()
            await db.execute("UPDATE channels SET last_chain = $2, chain_length = chain_length + 1 WHERE id = $1", msg.channel.id, msg.author.id)
            if (msg.content == "100" and chain.startswith("$")) or length == 100:
                await msg.add_reaction("💯")
            else:
                await msg.add_reaction("✅")

    async def dad_mode(self, message):
        """
        dad mode
        """
        async with self.bot.pool.acquire() as db:
            if not await db.fetchval("SELECT dad_mode FROM users WHERE id = $1", message.author.id):
                return
        phrases = {
            "i am {}": "Hi {}! I am Dad",
            "i'm {}": "Hi {}! I'm Dad",
            "im {}": "Hi {}! Im Dad",
            "わたしは{}です": "こんにちわ{}さん！わたしはおとうさんです",
            "私は{}です": "こんにちわ{}さん！私はお父さんです"
        }
        for said, reply in zip(phrases.keys(), phrases.values()):
            match = re.search(said.format(r"(.*)"), message.content.lower())
            if match:
                await message.channel.send(reply.format(match.group(1)))

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        runs stuff that has to run on_message
        """
        await self.dad_mode(message)
        await self.chain_check(message)


def setup(bot):
    """
    Load extension
    """
    bot.add_cog(Fun(bot))
