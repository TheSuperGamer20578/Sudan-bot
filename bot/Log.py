"""
Logs stuff
"""
import discord
from discord.ext import commands

from _Util import Checks, GREEN

logtypes = ["invites", "moderation"]


def find_invite_by_code(invite_list, code):
    """
    Gets an invite object from its code
    """
    for inv in invite_list:
        if inv.code == code:
            return inv
    return None


class Log(commands.Cog):
    """
    Main class
    """
    def __init__(self, bot):
        self.bot = bot
        self.invites = {}

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Save all active invites to a variable
        """
        for guild in self.bot.guilds:
            self.invites[guild.id] = await guild.invites()

    @commands.command(hidden=True)
    @commands.check(Checks.trusted)
    async def initlogs(self, ctx):
        """
        Run on_ready for if cog has been loaded after startup
        """
        await self.on_ready()
        await ctx.message.delete()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """
        Finds who invited a user
        """
        async with self.bot.pool.acquire() as db:
            channels =  await db.fetchval("SELECT count(*) FROM channels WHERE guild_id = $1 AND log_type = 'invites'")
        if len(channels) == 0:
            return
        invites_before_join = self.invites[member.guild.id]
        invites_after_join = await member.guild.invites()
        for invite in invites_before_join:
            if invite.uses < find_invite_by_code(invites_after_join, invite.code).uses:
                embed = discord.Embed(title="Member joined", description=f"{member.mention}({member.name}) was invited by {invite.inviter.mention}({invite.inviter}) using invite https://discord.gg/{invite.code}")
                for channel in channels
                    await self.bot.get_channel(channel["id"]).send(embed=embed)
                self.invites[member.guild.id] = invites_after_join
                return

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """
        Updates list of invites when a user leaves
        """
        for invite in await member.guild.invites():
            if invite.inviter.id == member.id:
                await invite.delete()
        self.invites[member.guild.id] = await member.guild.invites()

    @commands.command()
    @commands.check(Checks.admin)
    async def log(self, ctx, channel: discord.TextChannel, log_type):
        """
        Tells the bot to log something to a channel
        """
        if log_type.lower() not in logtypes:
            raise commands.BadArgument()
        await self.bot.db.execute("UPDATE channels SET log_type = $3 WHERE id = $1 AND guild_id = $2", channel.id, ctx.guild.id, log_type.lower())
        embed = discord.Embed(title="Log setup", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(Log(bot))
