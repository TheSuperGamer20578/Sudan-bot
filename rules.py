"""
Makes a rule embed will be used to set punishments when moderation is added
"""
import discord
from discord.ext import commands
from firebase_admin import firestore, credentials, initialize_app
from core import BLUE, admin

try:
    cred = credentials.Certificate("Config/firebase.json")
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

    @commands.command()
    @commands.check(admin)
    async def rules(self, ctx, operation, id, cat=None, *, desc=None):
        """
        Modifies rules
        """
        if operation not in ["remove", "add"] or cat not in ["ban", "kick", "warn", "mute", "faq"]:
            raise commands.errors.BadArgument()
        d = fs_data.document(str(ctx.guild.id)).get().to_dict()
        if d is None:
            d = {}
        if operation == "remove":
            del d[id]
        elif operation == "add":
            d[id] = {"cat": cat, "desc": desc}
        fs_data.document(str(ctx.guild.id)).set(d)
        await ctx.message.delete()
        embed = discord.Embed(title="Rules updated")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.check(admin)
    async def sendrules(self, ctx, channel: discord.TextChannel):
        """
        Sends rules to the specified channel
        """
        d = fs_data.document(str(ctx.guild.id)).get().to_dict()
        embed = discord.Embed(title="Rules", colour=BLUE)
        m = ""
        for x in [d[x]["desc"] for x in d if d[x]["cat"] == "ban"]:
            m += f"{x}\n\n"
        if len(m):
            embed.add_field(name="Instant ban:", value=m, inline=False)
        m = ""
        for x in [d[x]["desc"] for x in d if d[x]["cat"] == "kick"]:
            m += f"{x}\n\n"
        if len(m):
            embed.add_field(name="Kick:", value=m, inline=False)
        m = ""
        for x in [d[x]["desc"] for x in d if d[x]["cat"] == "mute"]:
            m += f"{x}\n\n"
        if len(m):
            embed.add_field(name="Mute:", value=m, inline=False)
        m = ""
        for x in [d[x]["desc"] for x in d if d[x]["cat"] == "warn"]:
            m += f"{x}\n\n"
        if len(m):
            embed.add_field(name="Warning:", value=m, inline=False)
        for x in [(d[x]["desc"], x) for x in d if d[x]["cat"] == "faq"]:
            embed.add_field(name=x[1], value=x[0], inline=False)
        await ctx.message.delete()
        await channel.send(embed=embed)
        embed = discord.Embed(title=f"Rules sent to #{channel.name}")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def rule(self, ctx, id):
        """
        Shows info of a rule
        """
        d = fs_data.document(str(ctx.guild.id)).get().to_dict()
        embed = discord.Embed(title=id, description=d[id]["desc"], colour=BLUE)
        embed.add_field(name="punishment", value=d[id]["cat"])
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(rules(bot))
