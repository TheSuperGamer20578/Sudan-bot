import discord
import base64
import requests
import json
from core import green, red, blue, trusted, purple
from discord.ext import commands
from Config import apikeys


class dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        embed = discord.Embed(title="New server!", description=guild.name, colour=green)
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
        # embed = discord.Embed(title="Suggestion", colour=blue, description=suggestion)
        # embed.add_field(name="Server", value=ctx.guild.name)
        # embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        # await ctx.message.delete()
        # await self.bot.get_channel(753495188361707550).send(embed=embed)
        resp = requests.post(apikeys.jiraurl + "issue", data=json.dumps({"fields": {
            "project": {"key": "SDB"},
            "summary": suggestion,
            "issuetype": {"name": "Suggestion"},
            "customfield_10103": str(ctx.author.id),
            "customfield_10036": ctx.author.name,
            "customfield_10037": ctx.guild.name
        }}), auth=apikeys.jira, headers={"Content-Type": "application/json"})
        i = resp.json()
        embed = discord.Embed(title="Suggestion noted!",
                              description=f"[{i['key']}](https://thesupergamer20578.atlassian.net/browse/{i['key']}): {suggestion}")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command()
    async def bug(self, ctx, *, bug):
        """
        Reports a bug **DO NOT REPORT NON SERIOUS BUGS**
        """
        # embed = discord.Embed(title="Bug", colour=red, description=bug)
        # embed.add_field(name="Server", value=ctx.guild.name)
        # embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        # await ctx.message.delete()
        # await self.bot.get_channel(753495213984710706).send(embed=embed)
        resp = requests.post(apikeys.jiraurl + "issue", data=json.dumps({"fields": {
            "project": {"key": "SDB"},
            "summary": bug,
            "issuetype": {"name": "Bug"},
            "customfield_10103": str(ctx.author.id),
            "customfield_10036": ctx.author.name,
            "customfield_10037": ctx.guild.name
        }}), auth=apikeys.jira, headers={"Content-Type": "application/json"})
        i = resp.json()
        embed = discord.Embed(title="Bug noted!",
                              description=f"[{i['key']}](https://thesupergamer20578.atlassian.net/browse/{i['key']}): {bug}")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command()
    async def issue(self, ctx, key):
        """
        Displays info on a Jira issue with the provided key
        """
        resp = requests.get(apikeys.jiraurl + "issue/" + key, auth=apikeys.jira)
        if not key.startswith("SDB-"):
            raise commands.BadArgument()
        i = resp.json()["fields"]
        if i["issuetype"]["name"] == "Bug":
            embed = discord.Embed(title=f"Bug: {key}", description=i["summary"], colour=red,
                                  url=f"https://thesupergamer20578.atlassian.net/browse/{key}")
        elif i["issuetype"]["name"] == "Suggestion":
            embed = discord.Embed(title=f"Suggestion: {key}", description=i["summary"], colour=green,
                                  url=f"https://thesupergamer20578.atlassian.net/browse/{key}")
        elif i["issuetype"]["name"] == "Epic":
            embed = discord.Embed(title=f"Epic: {key}", description=i["summary"], colour=purple,
                                  url=f"https://thesupergamer20578.atlassian.net/browse/{key}")
        else:
            raise Exception()
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        if i["issuetype"]["name"] != "Epic":
            embed.add_field(name="Status", value=i["status"]["name"])
            embed.add_field(name="Priority", value=i["priority"]["name"])
            embed.add_field(name="Author", value=f"<@{i['customfield_10103']}>({i['customfield_10036']})")
            embed.add_field(name="Server", value=i["customfield_10037"])
            try:
                i["parent"]
            except KeyError:
                pass
            else:
                embed.add_field(name="Epic",
                                value=f"[{i['parent']['key']}](https://thesupergamer20578.atlassian.net/browse/{i['parent']['key']}): " +
                                      i["parent"]["fields"]["summary"])
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.check(trusted)
    async def leaveserver(self, ctx, guild: int):
        guild = self.bot.get_guild(guild)
        await guild.leave()
        embed = discord.Embed(title=f"left {guild.name} owned by: {guild.owner.name}")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(dev(bot))
