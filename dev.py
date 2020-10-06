"""
Several tools to help with development and to track growth
"""
import json
import configparser
import discord
import requests
from discord.ext import commands
from requests.auth import HTTPBasicAuth
from core import GREEN, RED, trusted, PURPLE

config = configparser.ConfigParser()
config.read("Config/config.ini")

auth = HTTPBasicAuth(config["api"]["jira email"], config["api"]["jira key"])


class dev(commands.Cog):
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
        embed.set_author(name=guild.owner.nick if guild.owner.nick else guild.owner.name,
                         icon_url=guild.owner.avatar_url)
        embed.set_footer(text=f"ID: {guild.id}")
        await self.bot.get_channel(753495117767377016).send(embed=embed)

    @commands.command()
    async def suggest(self, ctx, *, suggestion):
        """
        Makes a suggestion issue on my Jira **DO NOT GIVE NON SERIOUS SUGGESTIONS**
        """
        resp = requests.post(config["api"]["jira url"] + "issue", data=json.dumps({"fields": {
            "project": {"key": "SDB"},
            "summary": suggestion,
            "issuetype": {"name": "Suggestion"},
            "customfield_10103": str(ctx.author.id),
            "customfield_10036": ctx.author.name,
            "customfield_10037": ctx.guild.name
        }}), auth=auth, headers={"Content-Type": "application/json"})
        issue = resp.json()
        embed = discord.Embed(title="Suggestion noted!",
                              description=f"[{issue['key']}](https://thesupergamer20578.atlassian.net/browse/{issue['key']}): {suggestion}")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command()
    async def bug(self, ctx, *, bug):
        """
        Reports a bug **DO NOT REPORT NON SERIOUS BUGS**
        """
        resp = requests.post(config["api"]["jira url"] + "issue", data=json.dumps({"fields": {
            "project": {"key": "SDB"},
            "summary": bug,
            "issuetype": {"name": "Bug"},
            "customfield_10103": str(ctx.author.id),
            "customfield_10036": ctx.author.name,
            "customfield_10037": ctx.guild.name
        }}), auth=auth, headers={"Content-Type": "application/json"})
        issue = resp.json()
        embed = discord.Embed(title="Bug noted!",
                              description=f"[{issue['key']}](https://thesupergamer20578.atlassian.net/browse/{issue['key']}): {bug}")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command()
    async def issue(self, ctx, key):
        """
        Displays info on a Jira issue with the provided key
        """
        resp = requests.get(config["api"]["jira url"] + "issue/" + key, auth=auth)
        if not key.startswith("SDB-"):
            raise commands.BadArgument()
        issue = resp.json()["fields"]
        if issue["issuetype"]["name"] == "Bug":
            embed = discord.Embed(title=f"Bug: {key}", description=issue["summary"], colour=RED,
                                  url=f"https://thesupergamer20578.atlassian.net/browse/{key}")
        elif issue["issuetype"]["name"] == "Suggestion":
            embed = discord.Embed(title=f"Suggestion: {key}", description=issue["summary"], colour=GREEN,
                                  url=f"https://thesupergamer20578.atlassian.net/browse/{key}")
        elif issue["issuetype"]["name"] == "Epic":
            embed = discord.Embed(title=f"Epic: {key}", description=issue["summary"], colour=PURPLE,
                                  url=f"https://thesupergamer20578.atlassian.net/browse/{key}")
        else:
            raise Exception()
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        if issue["issuetype"]["name"] != "Epic":
            embed.add_field(name="Status", value=issue["status"]["name"])
            embed.add_field(name="Priority", value=issue["priority"]["name"])
            embed.add_field(name="Author", value=f"<@{issue['customfield_10103']}>({issue['customfield_10036']})")
            embed.add_field(name="Server", value=issue["customfield_10037"])
            try:
                issue["parent"]
            except KeyError:
                pass
            else:
                embed.add_field(name="Epic",
                                value=f"[{issue['parent']['key']}](https://thesupergamer20578.atlassian.net/browse/{issue['parent']['key']}): " +
                                      issue["parent"]["fields"]["summary"])
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.check(trusted)
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


def setup(bot):
    """
    Initializes the cog
    """
    bot.add_cog(dev(bot))
