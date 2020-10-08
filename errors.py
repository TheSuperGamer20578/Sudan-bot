"""
Handles command errors
"""
import sys
import traceback
import asyncio
import configparser
from json import dumps
import requests

import discord
from discord.ext import commands

from core import RED, BLUE

config = configparser.ConfigParser()
config.read("Config/config.ini")

auth = {"Authorization": f"GenieKey {config['api']['opsgenie']}"}

emcstats = ["t", "res", "n", "online", "alliance"]
OPS = "https://api.eu.opsgenie.com/v2/"


class errors(commands.Cog):
    """
    Error handling cog
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """
        The part that handles errors
        """
        if hasattr(ctx.command, 'on_error'):
            return

        # idk what this does but it might be important but pycharm doesnt like it
        # cog = ctx.cog
        # if cog and cog._get_overridden_method(cog.cog_command_error) is not None:
        #     return

        error = getattr(error, 'original', error)

        if isinstance(error, commands.NoPrivateMessage):
            try:
                embed = discord.Embed(title=f'{ctx.command} can not be used in Private Messages.', colour=RED)
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
            if 656231016385478657 in [member.id for member in ctx.guild.members]:
                if ctx.message.content.split(" ")[0][1:] in emcstats and ctx.message.content[0] == "/":
                    return
            embed = discord.Embed(title=f"{ctx.message.content.split(' ')[0][1:]} doesnt exist or isn't loaded",
                                  colour=RED)

        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(title=f"Invalid argument for {ctx.command}", colour=RED)

        else:
            embed = discord.Embed(title="You caused an error!", colour=RED)
            trace = traceback.format_exception(type(error), error, error.__traceback__)
            resp = requests.post(OPS+"alerts", dumps({
                "message": f"Error in {ctx.command}",
                "description": "\n".join(trace),
                "alias": f"{type(error)} in {ctx.command} with {len(ctx.args)} arguments",
                "entity": "Sudan bot",
                "source": f"{ctx.guild.name} #{ctx.channel.name}",
                "details": {"user": f"{ctx.author.name}({ctx.author.nick})", "message": ctx.message.content}
            }), headers={**auth, "Content-Type": "application/json"})
            if resp.status_code != 202:
                sys.stderr.write(str(resp.content)+"\n")

        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass
        await ctx.send(embed=embed)


class log:
    """
    An attempt to redirect stout and stderr to discord it didnt work i might be able to make it work and goto Opsgenie
    """
    colour = {"error": RED, "info": BLUE}
    title = {"error": "Error(non-command)", "info": "Info"}

    def __init__(self, bot, t):
        self.type = t
        self.bot = bot

    def write(self, buf):
        """
        The part that was supposed to send stuff to discord
        """
        text = buf.rstrip()
        colour = self.colour[self.type]
        title = self.title[self.type]
        embed = discord.Embed(title=title, description=f"```python\n{text}\n```", colour=colour)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.bot.get_channel(753495157332246548).send(embed=embed))


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(errors(bot))
    # sys.stdout = log(bot, "info")
    # sys.stderr = log(bot, "error")
