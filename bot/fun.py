"""
Contains fun stuff
"""
import re
import asyncio

import discord
from discord.ext import commands


class fun(commands.Cog):
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

    @commands.command()
    async def chain(self, ctx, *, thing):
        """
        Starts a chain
        """
        await self.bot.db.execute("UPDATE channels SET last_chain = NULL WHERE id = $1", ctx.channel.id)
        await self.bot.db.execute(
            "UPDATE channels SET chain = $2 WHERE id = $1", ctx.channel.id,
            thing)
        if thing.startswith("$counting:"):
            await ctx.send(f"Counting started at: {thing.split(':')[1]}")
        else:
            await ctx.send(f"New chain: {thing}")

    async def chain_check(self, msg):
        """
        Checks to see if chain is broken
        """
        chain = await self.bot.db.fetchval("SELECT chain FROM channels WHERE id = $1", msg.channel.id)

        async def cbreak():
            """
            If the chain is broken say so and update DB
            """
            if msg.content.endswith(f"chain {chain}"):
                return
            await msg.add_reaction("❌")
            await msg.channel.send(
                f"{msg.author.mention} broke the chain! start a new chain with `.chain <thing>`. Chain length: {await self.bot.db.fetchval('SELECT chain_length FROM channels WHERE id = $1', msg.channel.id)}")
            break_role = await self.bot.db.fetchval("SELECT chain_break_role FROM guilds WHERE id = $1", msg.guild.id)
            if break_role is not None:
                await msg.author.add_roles(msg.guild.get_role(break_role))
            await self.bot.db.execute(
                "UPDATE channels SET chain = NULL, chain_length = 0 WHERE id = $1",
                msg.channel.id)

        if chain is None or msg.author.bot:
            return
        if chain.startswith("$counting:"):
            num = int(chain.split(":")[1])
            if msg.content != str(num + 1):
                await cbreak()
            else:
                num += 1
                await self.bot.db.execute("UPDATE channels SET chain = $2 WHERE id = $1", msg.channel.id, f"$counting:{num}")
        elif msg.content != chain or msg.author.id == await self.bot.db.fetchval("SELECT last_chain FROM channels WHERE id = $1", msg.channel.id):
            await cbreak()
        else:
            await self.bot.db.execute("UPDATE channels SET last_chain = $2, chain_length = chain_length + 1 WHERE id = $1", msg.channel.id, msg.author.id)
            if msg.content == "100":
                await msg.add_reaction("💯")
            else:
                await msg.add_reaction("✅")

    async def dad_mode(self, message):
        """
        dad mode
        """
        if not await self.bot.db.fetchval("SELECT dad_mode FROM users WHERE id = $1", message.author.id):
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
        await asyncio.sleep(.1)
        await self.dad_mode(message)
        await asyncio.sleep(.1)
        await self.chain_check(message)

    @commands.command()
    async def dadmode(self, ctx):
        """
        Toggles Dad mode.
        """
        await self.bot.db.execute("UPDATE users SET dad_mode = NOT dad_mode WHERE id = $1", ctx.author.id)
        await ctx.send("dad toggled!")


def setup(bot):
    """
    Load extension
    """
    bot.add_cog(fun(bot))
