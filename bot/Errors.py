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


def format_traceback(trace):
    """Does some formatting on a traceback"""
    hidden = 0
    final_trace = []
    for frame in trace:
        if "site-packages" in frame or "dist-packages" in frame:
            hidden += 1
            continue
        if hidden > 0:
            final_trace.append(f"\n{hidden} library frames hidden\n\n")
            hidden = 0
        final_trace.append(frame.replace(os.getcwd(), ""))
    return "".join(final_trace)


class Errors(commands.Cog):
    """
    Error handling cog
    """
    def __init__(self, bot):
        self.bot = bot
        bot.on_error = self.on_error
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
            trace = format_traceback(traceback.format_exception(type(error), error, error.__traceback__))
            await self.bot.log.exception(f"Exception in command: `{ctx.command}`\n"
                                         f"Message: `{ctx.message.content}` | `{ctx.message.id}`\n"
                                         f"User: `{ctx.author.name}#{ctx.author.discriminator}` | `{ctx.author.id}`\n"
                                         f"Server: `{ctx.guild.name}` | `{ctx.guild.id}`\n"
                                         f"```py\n{trace}```")

        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass
        await ctx.send(embed=embed)

    async def on_error(self, event, *args, error=None, **_):
        """Handle event errors"""
        if isinstance(error, BaseException):
            trace = traceback.format_exception(type(error), error, error.__traceback__)
        else:
            args = (error, *args)
            trace = traceback.format_exception(*sys.exc_info())
        trace = format_traceback(trace)
        if event == "on_message":
            message = args[0]
            info = (f"User: `{message.author.name}#{message.author.discriminator}` | `{message.author.id}`\n"
                    f"Server: `{message.guild.name}` | `{message.guild.id}`\n"
                    f"Message ID: `{message.id}`")
            await message.reply("An unknown error has occurred")
        elif event in ("on_button_click", "on_select_option"):
            interaction = args[0]
            info = (f"User: `{interaction.user.name}#{interaction.user.discriminator}` | `{interaction.user.id}`\n"
                    f"Server: `{interaction.guild.name}` | `{interaction.guild.id}`\n"
                    f"Custom ID: `{interaction.custom_id}`\n"
                    f"Message ID: `{interaction.message.id}`")
            try:
                await interaction.respond(content="An unknown error has occurred")
            except discord.NotFound:
                pass
        else:
            info = f"**Unknown event**\nArgs: `{args!r}`"
        await self.bot.log.exception(f"Exception in event: `{event}`\n{info}\n```py\n{trace}```")


class Redirect:
    """Redirects stdout and stderr to discord"""
    def __init__(self, method):
        self.method = method

    def write(self, text):
        """Logs error or info"""
        if len(text.strip()) == 0:
            return
        self.method(text.strip())

    def flush(self):
        """Does nothing, exists to stop bot from crashing"""


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(Errors(bot))
