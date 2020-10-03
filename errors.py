import discord
import sys
import traceback
from discord.ext import commands
from core import red, blue
import asyncio
import requests
from json import dumps
from Config import apikeys
emcstats = ["t", "res", "n", "online", "alliance"]
OPS = "https://api.eu.opsgenie.com/v2/"


class errors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, 'on_error'):
            return

        cog = ctx.cog
        if cog and cog._get_overridden_method(cog.cog_command_error) is not None:
            return

        error = getattr(error, 'original', error)

        if isinstance(error, commands.DisabledCommand):
            embed = discord.Embed(title=f"{ctx.command} is disabled", colour=red)

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                embed = discord.Embed(title=f'{ctx.command} can not be used in Private Messages.', colour=red)
                await ctx.author.send(embed=embed)
                return
            except discord.HTTPException:
                return

        elif isinstance(error, commands.errors.MissingRequiredArgument):
            embed = discord.Embed(title=f"{ctx.command} needs more arguments", colour=red)

        elif isinstance(error, commands.errors.CheckFailure):
            embed = discord.Embed(title=f"You do not have permission to use {ctx.command}", colour=red)

        elif isinstance(error, commands.errors.CommandNotFound):
            if 656231016385478657 in [x.id for x in ctx.guild.members]:
                if ctx.message.content.split(" ")[0][1:] in emcstats and ctx.message.content[0] == "/":
                    return
            embed = discord.Embed(title=f"{ctx.message.content.split(' ')[0][1:]} doesnt exist or isn't loaded",
                                  colour=red)

        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(title=f"Invalid argument for {ctx.command}", colour=red)

        else:
            embed = discord.Embed(title="You caused an error!", colour=red)
            # nl = "\n"
            # bs = "\\"
            # tb = [x.split(", ") for x in traceback.format_exception(type(error), error, error.__traceback__)]
            t = traceback.format_exception(type(error), error, error.__traceback__)
            # t = list(map(lambda x: 'File "' + ", ".join(["/".join(x[0].split("\\")[-2:]).split("/")[-1]] + x[1:]), [x.split(", ") for x in traceback.format_exception(type(error), error, error.__traceback__)]))
            # eembed = discord.Embed(title="Error", colour=red,
            #                        description=f"```python\n{nl.join(t).replace('`', '‘')}\n```")
            # # eembed = discord.Embed(title="Error", colour=red, description=f"```python\n{nl.join(traceback.format_stack()).replace('`', '‘')}\n```")
            # eembed.add_field(name="Error", inline=False, value=f"```python\n{type(error).__name__}: {error}\n```")
            # eembed.add_field(name="Server", value=ctx.guild.name)
            # eembed.add_field(name="Command", value=ctx.command)
            # eembed.add_field(name="User", value=ctx.author.name)
            # # print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            # # traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            # await self.bot.get_channel(753495157332246548).send(embed=eembed)
            resp = requests.post(OPS+"alerts", dumps({
                "message": f"Error in {ctx.command}",
                "description": "\n".join(t),
                "alias": f"{type(error)} in {ctx.command} with {len(ctx.args)} arguments",
                "entity": "Sudan bot",
                "source": f"{ctx.guild.name} #{ctx.channel.name}",
                "details": {"user": f"{ctx.author.name}({ctx.author.nick})", "message": ctx.message.content}
            }), headers={**apikeys.opsgenie, "Content-Type": "application/json"})
            if resp.status_code != 202:
                sys.stderr.write(str(resp.content)+"\n")

        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass
        await ctx.send(embed=embed)


class log(object):
    colour = {"error": red, "info": blue}
    title = {"error": "Error(non-command)", "info": "Info"}

    def __init__(self, bot, type):
        self.type = type
        self.bot = bot

    def write(self, buf):
        text = buf.rstrip()
        colour = self.colour[self.type]
        title = self.title[self.type]
        embed = discord.Embed(title=title, description=f"```python\n{text}\n```", colour=colour)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.bot.get_channel(753495157332246548).send(embed=embed))


def setup(bot):
    bot.add_cog(errors(bot))
    # sys.stdout = log(bot, "info")
    # sys.stderr = log(bot, "error")
