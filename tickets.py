"""
A ticket system
"""
import discord
import random
from discord.ext import commands
from firebase_admin import *
from firebase_admin import firestore
from .core import red, green, admin

try:
    cred = credentials.Certificate("Config/firebase.json")
    initialize_app(cred)
except ValueError:
    pass
db = firestore.client()
fs_data = db.collection("tickets")


def moderator(ctx):
    """
    Check to see if user is a ticket service person
    """
    return int(fs_data.document(str(ctx.guild.id)).get().to_dict()["m_role"]) in [x.id for x in ctx.author.roles]


class tickets(commands.Cog):
    """
    Main class
    """
    def __init__(self, bot):
        self.bot = bot
        with open("Config/names.txt", "r") as f:
            self.names = f.read().split("\n")

    @commands.command()
    @commands.check(admin)
    async def tsetup(self, ctx, mod: discord.Role):
        """
        Enables tickets for the server
        """
        await ctx.message.delete()
        if not fs_data.document(str(ctx.guild.id)).get().exists:
            cat = await ctx.guild.create_category("Tickets")
            rol = await ctx.guild.create_role(name="Banned from opening tickets", colour=discord.Colour(0x979C9F))
            log = await ctx.guild.create_text_channel(name="ticket logs")
            fs_data.document(str(ctx.guild.id)).set({
                "category": str(cat.id),
                "b_role": str(rol.id),
                "m_role": str(mod.id),
                "log": str(log.id)
            })
            embed = discord.Embed(title="Tickets have been setup")
            embed.set_author(name=ctx.author.nick, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @commands.command()
    async def new(self, ctx):
        """
        Opens a new ticket
        """
        await ctx.message.delete()
        if not fs_data.document(str(ctx.guild.id)).get().exists:
            return
        d = fs_data.document(str(ctx.guild.id)).get().to_dict()
        if ctx.guild.get_role(int(d["b_role"])) in ctx.author.roles:
            embed = discord.Embed(title="You are banned from opening tickets!", colour=red)
            embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed, delete_after=30)
            return
        channel = await ctx.guild.create_text_channel(random.choice(self.names),
                                                      category=ctx.guild.get_channel(int(d["category"])),
                                                      overwrites={
                                                          ctx.author: discord.PermissionOverwrite(read_messages=True),
                                                          ctx.guild.get_role(
                                                              int(d["m_role"])): discord.PermissionOverwrite(
                                                              read_messages=True),
                                                          ctx.guild.get_role(ctx.guild.id): discord.PermissionOverwrite(
                                                              read_messages=False)
                                                      })
        await channel.send("@everyone", delete_after=0)
        embed = discord.Embed(title="Ticket",
                              description="A moderator or other member of staff will be with you shortly\nWhile you wait please state what you need help with")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        msg = await channel.send(embed=embed)
        await msg.pin()

    @commands.command()
    @commands.check(moderator)
    async def close(self, ctx, *, reason="Resolved", channel: discord.channel = None):
        """
        Closes a ticket
        """
        if channel is None:
            channel = ctx.channel
        if not fs_data.document(str(ctx.guild.id)).get().exists:
            return
        d = fs_data.document(str(ctx.guild.id)).get().to_dict()
        if channel.category_id != int(d["category"]):
            return
        embed = discord.Embed(title=channel.name, description=channel.topic)
        embed.add_field(name="Closed by", value=ctx.author.mention)
        embed.add_field(name="Close Reason", value=reason)
        await self.bot.get_channel(int(fs_data.document(str(ctx.guild.id)).get().to_dict()["log"])).send(embed=embed)
        await channel.delete()

    @commands.command()
    @commands.check(moderator)
    async def title(self, ctx, *, summery, channel: discord.channel = None):
        """
        Sets the title of a ticket
        """
        if channel is None:
            channel = ctx.channel
        if not fs_data.document(str(ctx.guild.id)).get().exists:
            return
        d = fs_data.document(str(ctx.guild.id)).get().to_dict()
        if channel.category_id != int(d["category"]):
            return
        await ctx.message.delete()
        await channel.edit(name=summery)

    @commands.command()
    @commands.check(moderator)
    async def sum(self, ctx, *, summery, channel: discord.channel = None):
        """
        Sets the summery of a ticket
        """
        if channel is None:
            channel = ctx.channel
        if not fs_data.document(str(ctx.guild.id)).get().exists:
            return
        d = fs_data.document(str(ctx.guild.id)).get().to_dict()
        if channel.category_id != int(d["category"]):
            return
        await ctx.message.delete()
        await channel.edit(topic=summery)

    @commands.command()
    @commands.check(moderator)
    async def tban(self, ctx, user: discord.Member):
        """
        Bans someone from opening tickets
        """
        await ctx.message.delete()
        if not fs_data.document(str(ctx.guild.id)).get().exists:
            return
        d = fs_data.document(str(ctx.guild.id)).get().to_dict()
        if ctx.guild.get_role(int(d["b_role"])) not in user.roles:
            await ctx.author.add_roles(ctx.guild.get_role(int(d["b_role"])))
            embed = discord.Embed(title=f"{user.nick if user.nick else user.name} has successfully been banned from opening tickets!", colour=green)
        else:
            await ctx.author.remove_roles(ctx.guild.get_role(int(d["b_role"])))
            embed = discord.Embed(title=f"{user.nick if user.nick else user.name} has successfully been unbanned from opening tickets!", colour=green)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(tickets(bot))
