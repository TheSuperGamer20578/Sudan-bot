"""
A ticket system
"""
import discord
from discord.ext import commands
from jinja2 import Environment, FileSystemLoader, select_autoescape

from _util import RED, GREEN, Checks, set_db

_DB = None
env = Environment(
    loader=FileSystemLoader("."),
    autoescape=select_autoescape(['html', 'xml'])
)


async def ticket_person(ctx):
    """
    Check to see if user is a ticket service person
    """
    return await _DB.fetchval(
            "SELECT support_role FROM guilds WHERE id = $1",
            ctx.guild.id) in [role.id for role in ctx.author.roles]


class tickets(commands.Cog):
    """
    Main class
    """
    def __init__(self, bot):
        global _DB  # pylint: disable=global-statement
        self.bot = bot
        set_db(bot.db)
        _DB = bot.db

    @commands.command()
    @commands.check(Checks.admin)
    async def tsetup(self, ctx):
        """
        Enables tickets for the server
        """
        await ctx.message.delete()
        if await self.bot.db.fetchval("SELECT ticket_category FROM guilds WHERE id = $1", ctx.guild.id) is not None:
            cat = await ctx.guild.create_category("Tickets")
            rol = await ctx.guild.create_role(name="Banned from opening tickets", colour=discord.Colour(0x979C9F))
            log = await ctx.guild.create_text_channel(name="ticket logs")
            await self.bot.db.execute("UPDATE guilds SET ticket_category = $2, ticket_log_channel = $3, ticket_ban_role = $4, ticket_index = 1 WHERE id = $1",
                                      ctx.guild.id, cat.id, log.id, rol.id)
            embed = discord.Embed(title="Tickets have been setup")
            embed.set_author(name=ctx.author.nick, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 24*60*60, commands.BucketType.user)
    async def new(self, ctx):
        """
        Opens a new ticket
        """
        config = await self.bot.db.fetchrow("SELECT ticket_category, support_roles, ticket_ban_role, ticket_index FROM guilds WHERE id = $1", ctx.guild.id)
        if config["ticket_category"] is None:
            return
        await ctx.message.delete()
        if ctx.guild.get_role(config["ticket_ban_role"]) in ctx.author.roles:
            embed = discord.Embed(title="You are banned from opening tickets!", colour=RED)
            embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed, delete_after=30)
            return
        overwrites = {ctx.guild.get_role(role): discord.PermissionOverwrite(read_messages=True) for role in config["support_roles"]}
        channel = await ctx.guild.create_text_channel(f"ticket-{config['ticket_index']}",
                                                      category=ctx.guild.get_channel(config["ticket_category"]),
                                                      overwrites={
                                                          ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                                                          ctx.guild.get_role(ctx.guild.id): discord.PermissionOverwrite(
                                                              read_messages=False),
                                                          **overwrites
                                                      })
        await channel.send("@everyone", delete_after=0, allowed_mentions=discord.AllowedMentions(everyone=True))
        embed = discord.Embed(title="Ticket",
                              description="A member of staff will be with you shortly\nWhile you wait please state what you need help with")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        msg = await channel.send(embed=embed)
        await msg.pin()
        await self.bot.db.execute("UPDATE guilds SET ticket_index = ticket_index + 1 WHERE id = $1", ctx.guild.id)

    @commands.command()
    @commands.check(ticket_person)
    async def close(self, ctx, *, reason="Resolved"):
        """
        Closes a ticket
        """
        config = await self.bot.db.fetchrow(
            "SELECT ticket_category, ticket_log_channel FROM guilds WHERE id = $1",
            ctx.guild.id)
        if config["ticket_category"] is None:
            return
        if ctx.channel.category_id != config["ticket_category"]:
            return
        template = env.get_template("ticket_transcript.html.jinja2")
        with open("transcript.html", "w") as transcript:
            transcript.write(template.render(
                name=ctx.channel.name,
                summury=ctx.channel.topic,
                messages=await ctx.channel.history(oldest_first=True).flatten()
            ).replace("    ", ""). replace("\n", ""))
        embed = discord.Embed(title=ctx.channel.name, description=ctx.channel.topic)
        embed.add_field(name="Closed by", value=ctx.author.mention)
        embed.add_field(name="Close Reason", value=reason)
        await self.bot.get_channel(config["ticket_log_channel"]).send(embed=embed, file=discord.File("transcript.html"))
        await ctx.channel.delete()

    @commands.command()
    @commands.check(ticket_person)
    async def sum(self, ctx, *, summery,):
        """
        Sets the summery of a ticket
        """
        config = await self.bot.db.fetchrow(
            "SELECT ticket_category FROM guilds WHERE id = $1", ctx.guild.id)
        if config["ticket_category"] is None:
            return
        if ctx.channel.category_id != config["ticket_category"]:
            return
        await ctx.message.delete()
        await ctx.channel.edit(topic=summery)

    @commands.command()
    @commands.check(ticket_person)
    async def tban(self, ctx, user: discord.Member):
        """
        Bans someone from opening tickets
        """
        config = await self.bot.db.fetchrow(
            "SELECT ticket_ban_role FROM guilds WHERE id = $1", ctx.guild.id)
        if config["ticket_ban_role"] is None:
            return
        await ctx.message.delete()
        if ctx.guild.get_role(config["ticket_ban_role"]) not in user.roles:
            await ctx.author.add_roles(ctx.guild.get_role(config["ticket_ban_role"]))
            embed = discord.Embed(title=f"{user.nick if user.nick else user.name} has successfully been banned from opening tickets!", colour=GREEN)
        else:
            await ctx.author.remove_roles(ctx.guild.get_role(config["ticket_ban_role"]))
            embed = discord.Embed(title=f"{user.nick if user.nick else user.name} has successfully been unbanned from opening tickets!", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(tickets(bot))
