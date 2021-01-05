"""
The core of the bot adds some essential commands and starts the bot you can load as an extension if you want
"""
import time
import os
from datetime import timezone

import discord
import asyncpg
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

BLUE = 0x0a8cf0
PURPLE = 0x6556FF
GREEN = 0x36eb45
RED = 0xb00e0e


async def _load_db():
    return await asyncpg.connect(user=os.getenv("DB_USERNAME"), password=os.getenv("DB_PASSWORD"),
                                 host=os.getenv("DB_HOST"), database=os.getenv("DB_DATABASE"))


async def _close_db(database):
    await database.close()


db = None


async def trusted(ctx):
    """
    Check to see if the user is trusted
    """
    return await db.fetchval("SELECT trusted FROM users WHERE id = $1", ctx.author.id)


async def mod(ctx):
    """
    Check to see if the user is a mod
    """
    return any([a in b for a, b in (await db.fetchval("SELECT mod_roles FROM guilds WHERE id = $1", ctx.guild.id), [role.id for role in ctx.author.roles])])


async def admin(ctx):
    """
    Check to see if the user is an admin
    """
    return any([a in b for a, b in (await db.fetchval("SELECT admin_roles FROM guilds WHERE id = $1", ctx.guild.id), [role.id for role in ctx.author.roles])])


class core(commands.Cog):
    """
    Contains essential commands
    """
    def __init__(self, b):
        self.bot = b
        self.bot.remove_command("help")

    @commands.command()
    async def help(self, ctx, page=None):
        """
        Provides help
        """
        if page == "all":
            embed = discord.Embed(title="All help", colour=BLUE)
            for cat in self.bot.cogs:
                if len([command for command in self.bot.walk_commands() if command.cog_name == cat and not command.hidden]) > 0:
                    embed.add_field(name=cat, value="\n".join([f"**{command.name}**{': ' + command.help if command.help is not None else ''}" for command in self.bot.walk_commands() if command.cog_name == cat and not command.hidden]))
            embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
            await ctx.message.delete()
            await ctx.send(embed=embed)
            return
        if page is not None:
            embed = discord.Embed(title=f"Help for {page}", colour=BLUE, description="\n".join([f"**{command.name}**{': ' + command.help if command.help is not None else ''}" for command in self.bot.walk_commands() if command.cog_name == page and not command.hidden]))
            embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
            await ctx.message.delete()
            await ctx.send(embed=embed)
        if page is None:
            embed = discord.Embed(title="Help index", colour=BLUE, description="To see help for everything type `.help all` to see help for a category type `.help <category>`\n\n__**Categories:**__\n" + "\n".join(self.bot.cogs))
            embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
            await ctx.message.delete()
            await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.check(trusted)
    async def load(self, ctx, extension):
        """
        Loads or reloads a cog
        """
        await ctx.message.delete()
        if extension in self.bot.cogs:
            self.bot.unload_extension(extension)
        try:
            self.bot.load_extension(extension)
        except commands.ExtensionNotFound:
            embed = discord.Embed(title=f"\"{extension}\" was not  found", colour=RED)
        else:
            embed = discord.Embed(title=f"\"{extension}\" was successfully loaded!", colour=GREEN)
        embed.set_author(name=ctx.author.nick, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.check(trusted)
    async def unload(self, ctx, extension):
        """
        Unloads a cog
        """
        await ctx.message.delete()
        try:
            self.bot.unload_extension(extension)
        except commands.ExtensionNotLoaded:
            embed = discord.Embed(title=f"The cog \"{extension}\" is not loaded", colour=RED)
        else:
            embed = discord.Embed(title=f"The cog \"{extension}\" was successfully unloaded!", colour=GREEN)
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
        for extension in self.bot.cogs:
            msg += f"✅ {extension}\n"
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

    @commands.group(hidden=True)
    @commands.check(trusted)
    async def trust(self, ctx):
        pass

    @trust.command(hidden=True, aliases=["add", "remove"])
    @commands.check(trusted)
    async def toggle(self, ctx, user: discord.Member):
        """
        Adds or removes a user from trusted list
        """
        if await self.bot.db.fetchval("SELECT trusted FROM users WHERE id = $1", user.id):
            embed = discord.Embed(title=f"{user.nick if user.nick else user.name} is no longer trusted")
            await self.bot.db.execute("UPDATE users SET trusted = FALSE WHERE id = $1", user.id)
        else:
            embed = discord.Embed(title=f"{user.nick if user.nick else user.name} is now trusted")
            await self.bot.db.execute("UPDATE users SET trusted = TRUE WHERE id = $1", user.id)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @trust.command(hidden=True, name="list")
    @commands.check(trusted)
    async def trust_list(self, ctx):
        """
        Lists all trusted users
        """
        records = await self.bot.db.fetch("SELECT id FROM users WHERE trusted = true")
        users = [f"<@{user['id']}>" for user in records]
        embed = discord.Embed(title="Trusted users", description="\n".join(users))
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx):
        """
        Gives invite for you to invite bot to your own server
        """
        await ctx.message.delete()
        embed = discord.Embed(title="Add me to your server by clicking here", url="https://discord.com/api/oauth2/authorize?client_id=693313847028744212&permissions=0&scope=bot", colour=BLUE)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Sets the status of the bot and adds stuff to the db
        """
        for guild in self.bot.guilds:
            try:
                await self.bot.db.execute("INSERT INTO guilds (id, delete_blank_messages) VALUES ($1, false)", guild.id)
            except asyncpg.UniqueViolationError:
                pass
            for member in guild.members:
                try:
                    await self.bot.db.execute("INSERT INTO users (id, trusted, dad_mode) VALUES ($1, false, false)", member.id)
                except asyncpg.UniqueViolationError:
                    pass
            for channel in guild.text_channels:
                try:
                    await self.bot.db.execute("INSERT INTO channels (id, guild_id) VALUES ($1, $2)", channel.id, guild.id)
                except asyncpg.UniqueViolationError:
                    pass

        types = {
            "playing": discord.ActivityType.playing,
            "watching": discord.ActivityType.watching,
            "streaming": discord.ActivityType.streaming,
            "listening": discord.ActivityType.listening,
            "competing": discord.ActivityType.competing,
            "custom": discord.ActivityType.custom
        }
        activity = discord.Activity(type=types[os.getenv("ACTIVITY_TYPE")], name=os.getenv("ACTIVITY"))
        statuses = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "invisible": discord.Status.invisible
        }
        await self.bot.change_presence(status=statuses[os.getenv("STATUS")], activity=activity)

    @commands.command()
    async def github(self, ctx):
        """
        Links to github
        """
        embed = discord.Embed(title="Click here to goto my Github", url="https://github.com/TheSuperGamer20578/Sudan-bot", colour=BLUE)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """
        Adds new guilds to the db
        """
        try:
            await self.bot.db.execute("INSERT INTO guilds (id, delete_blank_messages) VALUES ($1, false)", guild.id)
        except asyncpg.UniqueViolationError:
            pass
        for member in guild.members:
            try:
                await self.bot.db.execute("INSERT INTO users (id, trusted, dad_mode) VALUES ($1, false, false)", member.id)
            except asyncpg.UniqueViolationError:
                pass
        for channel in guild.text_channels:
            try:
                await self.bot.db.execute("INSERT INTO channels (id, guild_id) VALUES ($1, $2)", channel.id, guild.id)
            except asyncpg.UniqueViolationError:
                pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """
        adds new users to the db
        """
        try:
            await self.bot.db.execute("INSERT INTO users (id, trusted, dad_mode) VALUES ($1, false, false)", member.id)
        except asyncpg.UniqueViolationError:
            pass

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """
        Adds new channels to the db
        """
        if isinstance(channel, discord.TextChannel):
            try:
                await self.bot.db.execute("INSERT INTO channels (id, guild_id) VALUES ($1, $2)", channel.id, guild.id)
            except asyncpg.UniqueViolationError:
                pass


def setup(setup_bot):
    """
    Initiate cog if loaded as extension
    """
    bot.add_cog(core(setup_bot))


if __name__ == '__main__':
    bot = commands.Bot(command_prefix=os.getenv("PREFIXES").split(","))
    bot.add_cog(core(bot))
    for cog in os.getenv("AUTOLOAD_COGS").split(","):
        if cog != "":
            bot.load_extension(cog)
    bot.db = bot.loop.run_until_complete(_load_db())
    db = bot.db
    bot.run(os.getenv("BOT_TOKEN"))
    bot.loop.run_until_complete(_close_db(bot.db))
