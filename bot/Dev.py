"""
Several tools to help with development and to track growth
"""
import ast
import traceback
import os

import discord
from discord.ext import commands
from requests.auth import HTTPBasicAuth

from _Util import GREEN, RED, Checks, BLUE
from _Logger import LEVELS

auth = HTTPBasicAuth(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_TOKEN"))


def insert_returns(body):
    """
    Eval magic
    """
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)


class Dev(commands.Cog):
    """
    Main class for this file
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """
        Sends message when the bot is added to a server
        """
        embed = discord.Embed(title="New server!", description=guild.name, colour=GREEN)
        embed.add_field(name="Owner", value=guild.owner.name)
        embed.add_field(name="Members", value=str(len(guild.members)))
        embed.set_author(name=guild.owner.nick if guild.owner.nick else guild.owner.name, icon_url=guild.owner.avatar_url)
        embed.set_footer(text=f"ID: {guild.id}")
        await self.bot.get_channel(753495117767377016).send(embed=embed)

    @commands.command()
    async def issues(self, ctx):
        """
        Links to issue tracker
        """
        await ctx.message.delete()
        await ctx.send("Issue tracker: https://github.com/TheSuperGamer20578/Sudan-bot/issues")

    @commands.command()
    async def bug(self, ctx):
        """
        File a bug report
        """
        await ctx.message.delete()
        await ctx.send("File a bug report: https://github.com/TheSuperGamer20578/Sudan-bot/issues/new?labels=Bug&template=bug_report.md")

    @commands.command()
    async def suggest(self, ctx):
        """
        Make a suggestion
        """
        await ctx.message.delete()
        await ctx.send("Make a suggestion: https://github.com/TheSuperGamer20578/Sudan-bot/issues/new?labels=Enhancement&template=feature_request.md")

    @commands.command(hidden=True)
    @commands.check(Checks.trusted)
    async def leaveserver(self, ctx, guild: int):
        """
        Make the bot leave a server
        """
        guild = self.bot.get_guild(guild)
        await guild.leave()
        embed = discord.Embed(title=f"left {guild.name} owned by: {guild.owner.name}")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.check(Checks.trusted)
    async def loglevel(self, ctx, level):
        """Changes the log level"""
        assert level in LEVELS
        await self.bot.log.change_level(level, ctx.author.name)
        await ctx.send(f"Set log level to {level}")

    @commands.command(hidden=True)
    @commands.check(Checks.trusted)
    async def eval(self, ctx, *, cmd):
        """
        Evaluates input
        """
        fn_name = "_eval_expr"
        cmd = cmd.strip("` ")
        ecmd = cmd
        cmd = "\n".join(f"    {i}" for i in cmd.splitlines())
        body = f"async def {fn_name}():\n{cmd}"
        parsed = ast.parse(body)
        body = parsed.body[0].body
        insert_returns(body)
        env = {
            "bot": ctx.bot,
            "discord": discord,
            "commands": commands,
            "ctx": ctx,
            "__import__": __import__
        }
        exec(compile(parsed, filename="<ast>", mode="exec"), env)
        result = (await eval(f"{fn_name}()", env))
        embed = discord.Embed(title="Evaluation", colour=BLUE)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.add_field(name="Input", value=f"```python\n{ecmd}\n```", inline=False)
        embed.add_field(name="Output", value=f"```python\n{result}\n```", inline=False)
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @eval.error
    async def eval_error(self, ctx, error):
        """
        Handles errors in eval
        """
        if isinstance(error, commands.CheckFailure):
            embed = discord.Embed(title="You do not have permission to use eval", colour=RED)
        else:
            cmd = ctx.message.content.split(" ", maxsplit=1)[1].strip("` ")
            trace = traceback.format_exception(type(error), error, error.__traceback__)
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
            embed = discord.Embed(title="Evaluation", description=f"**Error**\n```python\n{final_trace}```", colour=RED)
            embed.add_field(name="Input", value=f"```python\n{cmd}\n```", inline=False)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initializes the cog
    """
    bot.add_cog(Dev(bot))
