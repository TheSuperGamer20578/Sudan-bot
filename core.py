"""
The core of the bot adds some essential commands and starts the bot you can load as an extension if you want
"""
import time
import asyncio
import configparser
from datetime import timezone
import discord
from firebase_admin import firestore, credentials, initialize_app
from discord.ext import commands

config = configparser.ConfigParser()
config.read("Config/config.ini")

try:
    cred = credentials.Certificate("Config/firebase.json")
    initialize_app(cred)
except ValueError:
    pass
db = firestore.client()
fs_data = db.collection("core")

BLUE = 0x0a8cf0
PURPLE = 0x6556FF
GREEN = 0x36eb45
RED = 0xb00e0e


def trusted(ctx):
    """
    Check to see if the user is trusted
    """
    return str(ctx.author.id) in fs_data.document("trusted").get().to_dict()["users"]


def mod(ctx):
    """
    Check to see if the user is a mod
    """
    return db.collection("settings").document(str(ctx.guild.id)).get().to_dict()["modrole"] in [str(role.id) for role in ctx.author.roles]


def admin(ctx):
    """
    Check to see if the user is an admin
    """
    return db.collection("settings").document(str(ctx.guild.id)).get().to_dict()["adminrole"] in [str(i.id) for i in ctx.author.roles]


class core(commands.Cog):
    """
    Contains essential commands
    """
    def __init__(self, b):
        self.bot = b
        self.bot.remove_command("help")

    @commands.command()
    async def help(self, ctx, cog=None):
        """
        Provides help
        """
        if cog == "all":
            embed = discord.Embed(title="All help", colour=BLUE)
            for cog in self.bot.cogs:
                if len([command for command in self.bot.walk_commands() if command.cog_name == cog and not command.hidden]) > 0:
                    embed.add_field(name=cog, value="\n".join([f"**{command.name}**{': '+command.help if command.help is not None else ''}" for command in self.bot.walk_commands() if command.cog_name == cog and not command.hidden]))
            embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
            await ctx.message.delete()
            await ctx.send(embed=embed)
            return
        if cog is not None:
            embed = discord.Embed(title=f"Help for {cog}", colour=BLUE, description="\n".join([f"**{command.name}**{': ' + command.help if command.help is not None else ''}" for command in self.bot.walk_commands() if command.cog_name == cog and not command.hidden]))
            embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
            await ctx.message.delete()
            await ctx.send(embed=embed)
        if cog is None:
            embed = discord.Embed(title="Help index", colour=BLUE, description="To see help for everything type `.help all` to see help for a category type `.help <category>`\n\n__**Categories:**__\n" + "\n".join(self.bot.cogs))
            embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
            await ctx.message.delete()
            await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.check(trusted)
    async def load(self, ctx, cog):
        """
        Loads or reloads a cog
        """
        await ctx.message.delete()
        if cog in self.bot.cogs:
            self.bot.unload_extension(cog)
        try:
            self.bot.load_extension(cog)
        except commands.ExtensionNotFound:
            embed = discord.Embed(title=f"\"{cog}\" was not  found", colour=RED)
        else:
            embed = discord.Embed(title=f"\"{cog}\" was successfully loaded!", colour=GREEN)
        embed.set_author(name=ctx.author.nick, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.check(trusted)
    async def unload(self, ctx, cog):
        """
        Unloads a cog
        """
        await ctx.message.delete()
        try:
            self.bot.unload_extension(cog)
        except commands.ExtensionNotLoaded:
            embed = discord.Embed(title=f"The cog \"{cog}\" is not loaded", colour=RED)
        else:
            embed = discord.Embed(title=f"The cog \"{cog}\" was successfully unloaded!", colour=GREEN)
        embed.set_author(name=ctx.author.nick, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.check(trusted)
    async def list(self, ctx):
        """
        Lists all cogs
        """
        await ctx.message.delete()
        msg = ""
        for cog in self.bot.cogs:
            msg += f"✅ {cog}\n"
        for file in os.listdir():
            if file.endswith(".py") and file[:-3] not in self.bot.cogs and file != "start.py":
                msg += f"\n❎ {file[:-3]}"
        embed = discord.Embed(title="Cogs", description=msg)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        """
        Ping, pong
        """
        await ctx.send(
            f"Pong! (took {max(time.time() - ctx.message.created_at.replace(tzinfo=timezone.utc).timestamp(), ctx.message.created_at.replace(tzinfo=timezone.utc).timestamp() - time.time())} seconds)")

    @commands.command(hidden=True)
    @commands.check(trusted)
    async def trust(self, ctx, user: discord.Member):
        """
        Adds or removes a user from trusted list
        """
        if str(user.id) in fs_data.document("trusted").get().to_dict()["users"]:
            embed = discord.Embed(title=f"{user.nick if user.nick else user.name} is no longer trusted")
            fs_data.document("trusted").set(
                {"users": [str(trustee) for trustee in fs_data.document("trusted").get().to_dict()["users"] if i != str(user.id)]})
        else:
            embed = discord.Embed(title=f"{user.nick if user.nick else user.name} is now trusted")
            data = fs_data.document("trusted").get().to_dict()["users"]
            data.append(str(user.id))
            fs_data.document("trusted").set({"users": data})
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx):
        """
        Gives invite for you to invite bot to your own server
        """
        await ctx.message.delete()
        embed = discord.Embed(title="Add me to your server by clicking here",
                              url="https://discord.com/api/oauth2/authorize?client_id=693313847028744212&permissions=0&scope=bot",
                              colour=BLUE)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Sets the status of the bot
        """
        activity = discord.Activity(type=discord.ActivityType.watching, name="the rise of Sudan and the fall of noobia")
        await self.bot.change_presence(status=discord.Status.dnd, activity=activity)
        await asyncio.sleep(30)
        await self.bot.change_presence(status=discord.Status.online, activity=activity)

    @commands.command()
    async def github(self, ctx):
        """
        Links to github
        """
        embed = discord.Embed(title="Click here to goto my Github", url="https://github.com/TheSuperGamer20578/Sudan-bot", colour=BLUE)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)


def setup(setup_bot):
    """
    Initiate cog if loaded as extension
    """
    bot.add_cog(core(setup_bot))


if __name__ == '__main__':
    bot = commands.Bot(command_prefix=("&", "/", ".", "sb!", "s!"))  # , commands.when_mentioned))
    bot.add_cog(core(bot))
    for cog in config["general"]["autoload cogs"].split("\n"):
        if cog != "":
            bot.load_extension(cog)
    bot.run(config["api"]["discord"])
