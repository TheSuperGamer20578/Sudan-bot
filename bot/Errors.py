"""
Handles command errors
"""
import traceback
import os
import sys
import asyncio

import discord
from discord.ext import commands

from _Util import RED
from Moderation import human_delta


class Errors(commands.Cog):
    """
    Error handling cog
    """
    def __init__(self, bot):
        self.bot = bot
        if bot.is_ready():
            sys.stdout = Redirect(bot.log.stdout)
            sys.stderr = Redirect(bot.log.stderr)

    @commands.Cog.listener()
    async def on_ready(self):
        """Redirects stdout and stderr when bot is ready"""
        await asyncio.sleep(1)
        sys.stdout = Redirect(self.bot.log.stdout)
        sys.stderr = Redirect(self.bot.log.stderr)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """
        The part that handles errors
        """
        # pylint: disable=too-many-statements
        if hasattr(ctx.command, "on_error"):
            return

        error = getattr(error, "original", error)

        if isinstance(error, commands.NoPrivateMessage):
            try:
                embed = discord.Embed(title=f"{ctx.command} can not be used in Private Messages.", colour=RED)
                await ctx.author.send(embed=embed)
                return
            except discord.HTTPException:
                return

        if isinstance(error, commands.DisabledCommand):
            embed = discord.Embed(title=f"{ctx.command} is disabled", colour=RED)

        elif isinstance(error, commands.errors.MissingRequiredArgument):
            embed = discord.Embed(title=f"{ctx.command} needs more arguments", colour=RED)

        elif isinstance(error, commands.errors.CheckFailure):
            embed = discord.Embed(title=f"You do not have permission to use {ctx.command}", colour=RED)

        elif isinstance(error, commands.errors.CommandNotFound):
            embed = discord.Embed(title=f"{ctx.message.content.split(' ')[0][1:]} doesnt exist or isn't loaded",
                                  colour=RED)

        elif isinstance(error, (commands.BadArgument, AssertionError)):
            embed = discord.Embed(title=f"Invalid argument for {ctx.command}", colour=RED)

        elif isinstance(error, commands.CommandOnCooldown):
            time = error.retry_after
            types = {
                commands.BucketType.default: "global",
                commands.BucketType.guild: "server",
                commands.BucketType.channel: "channel",
                commands.BucketType.member: "member",
                commands.BucketType.category: "category",
                commands.BucketType.role: "role",
                commands.BucketType.user: "user"
            }
            embed = discord.Embed(title=f"{ctx.command} is on {types[error.cooldown.type]} cooldown for {human_delta(time)}", colour=RED)

        else:
            embed = discord.Embed(title="An unexpected error has occurred", colour=RED)
            trace = traceback.format_exception(type(error), error, error.__traceback__)
            hidden = 0
            final_trace = []
            for frame in trace:
                if "site-packages" in frame:
                    hidden += 1
                    continue
                if hidden > 0:
                    final_trace.append(f"\n{hidden} library frames hidden\n\n")
                    hidden = 0
                final_trace.append(frame.replace(os.getcwd(), ""))
            await self.bot.log.exception(f"Exception in command: `{ctx.command}`\n"
                                         f"Message: `{ctx.message.content}`\n"
                                         f"User: `{ctx.author.name}#{ctx.author.discriminator}`\n"
                                         f"Server: `{ctx.guild.name}`\n"
                                         f"```py\n{''.join(final_trace)}```")

        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass
        await ctx.send(embed=embed)


class Redirect:
    """Redirects stdout and stderr to discord"""
    def __init__(self, method):
        self.method = method

    def write(self, text):
        """Logs error or info"""
        if len(text.strip()) == 0:
            return
        self.method(text.strip())


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(Errors(bot))
