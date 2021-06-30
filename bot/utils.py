"""
Provides several utilities
"""
from typing import Optional, Union

import discord
from discord.ext import commands

from _util import Checks, BLUE, RED, GREEN
from moderation import parse_time, human_delta


def parse_purge_filter(arg):
    filters = {}

    def purge_filter(func):
        filters[func.__name__] = func
        return func

    @purge_filter
    def bots(message):
        return message.author.bot

    @purge_filter
    def humans(message):
        return not message.author.bot

    @purge_filter
    def embeds(message):
        return len(message.embeds) > 0

    return filters[arg]


class utils(commands.Cog):
    """
    Main class
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(Checks.mod)
    async def slowmode(self, ctx, time: commands.Greedy[parse_time]):
        """
        Sets the slowmode of a channel
        """
        time = sum(time)
        await ctx.message.delete()
        embed = discord.Embed(title=f"Slowmode set to {human_delta(time)}")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.channel.edit(slowmode_delay=time)
        await ctx.send(embed=embed)

    @commands.command()
    async def age(self, ctx, user: discord.Member):
        """
        Displays how long a member has had their discord account for and how long they have been in the server
        """
        embed = discord.Embed(title=user.display_name, description=f"**Created:** {user.created_at}\n**Joined:** {user.joined_at}", colour=BLUE)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command()
    @commands.check(Checks.admin)
    async def embed(self, ctx, channel: Optional[discord.TextChannel], title, colour: discord.Colour, *, description: str = discord.embeds.EmptyEmbed):
        if channel is None:
            channel = ctx.channel

        await ctx.message.delete()
        embed = discord.Embed(title=title, description=description, colour=colour)
        message = await channel.send(embed=embed)

        async with self.bot.pool.acquire() as db:
            await db.execute("INSERT INTO embeds (guild, id, colour) VALUES ($1, $2, $3)", ctx.guild.id, message.id, colour.value)

    @commands.command()
    @commands.check(Checks.admin)
    async def editembed(self, ctx, message: discord.Message, title, *, description: str = discord.embeds.EmptyEmbed):
        async with self.bot.pool.acquire() as db:
            colour = await db.fetchval("SELECT colour FROM embeds WHERE guild = $1 AND id = $2", ctx.guild.id, message.id)
        await ctx.message.delete()
        if colour is None:
            embed = discord.Embed(title="That embed does not exist!", colour=RED)
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(title=title, description=description, colour=colour)
        await message.edit(embed=embed)

    @commands.command()
    @commands.check(Checks.mod)
    async def purge(self, ctx, purge_filter: Optional[Union[parse_purge_filter, discord.Member]], limit: int):
        def none(message):
            return True

        def user(member):
            def predicate(message):
                return message.author == member
            return predicate

        if purge_filter is None:
            purge_filter = none
        elif isinstance(purge_filter, discord.Member):
            purge_filter = user(purge_filter)

        await ctx.message.delete()
        deleted = await ctx.channel.purge(limit=limit, check=purge_filter)
        embed = discord.Embed(title=f"Purged {len(deleted)} messages", colour=GREEN)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed, delete_after=1)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(utils(bot))
