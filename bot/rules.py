"""
Makes a rule embed will be used to set punishments when moderation is added
"""
import discord
from discord.ext import commands
from firebase_admin import firestore, credentials, initialize_app

from _util import BLUE, checks

try:
    cred = credentials.Certificate("firebase.json")
    initialize_app(cred)
except ValueError:
    pass
db = firestore.client()
fs_data = db.collection("rules")


class rules(commands.Cog):
    """
    Main class
    """
    def __init__(self, bot):
        self.bot = bot
        self.checks = checks(bot.db)

    @commands.command()
    @commands.check(self.checks.admin)
    async def rules(self, ctx, operation, _id, cat=None, *, desc=None):
        """
        Modifies rules
        """
        if operation not in ["remove", "add"] or cat not in ["ban", "kick", "warn", "mute", "faq"]:
            raise commands.errors.BadArgument()
        data = fs_data.document(str(ctx.guild.id)).get().to_dict()
        if data is None:
            data = {}
        if operation == "remove":
            del data[_id]
        elif operation == "add":
            data[_id] = {"cat": cat, "desc": desc}
        fs_data.document(str(ctx.guild.id)).set(data)
        await ctx.message.delete()
        embed = discord.Embed(title="Rules updated")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.check(self.checks.admin)
    async def sendrules(self, ctx, channel: discord.TextChannel):
        """
        Sends rules to the specified channel
        """
        data = fs_data.document(str(ctx.guild.id)).get().to_dict()
        embed = discord.Embed(title="Rules", colour=BLUE)
        field = ""
        for rule in [data[x]["desc"] for x in data if data[x]["cat"] == "ban"]:
            field += f"{rule}\n\n"
        if len(field) > 0:
            embed.add_field(name="Instant ban:", value=field, inline=False)
        field = ""
        for rule in [data[x]["desc"] for x in data if data[x]["cat"] == "kick"]:
            field += f"{rule}\n\n"
        if len(field) > 0:
            embed.add_field(name="Kick:", value=field, inline=False)
        field = ""
        for rule in [data[x]["desc"] for x in data if data[x]["cat"] == "mute"]:
            field += f"{rule}\n\n"
        if len(field) > 0:
            embed.add_field(name="Mute:", value=field, inline=False)
        field = ""
        for rule in [data[x]["desc"] for x in data if data[x]["cat"] == "warn"]:
            field += f"{rule}\n\n"
        if len(field) > 0:
            embed.add_field(name="Warning:", value=field, inline=False)
        for rule in [(data[x]["desc"], x) for x in data if data[x]["cat"] == "faq"]:
            embed.add_field(name=rule[1], value=rule[0], inline=False)
        await ctx.message.delete()
        await channel.send(embed=embed)
        embed = discord.Embed(title=f"Rules sent to #{channel.name}")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def rule(self, ctx, _id):
        """
        Shows info of a rule
        """
        data = fs_data.document(str(ctx.guild.id)).get().to_dict()
        embed = discord.Embed(title=_id, description=data[_id]["desc"], colour=BLUE)
        embed.add_field(name="punishment", value=data[_id]["cat"])
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(rules(bot))
