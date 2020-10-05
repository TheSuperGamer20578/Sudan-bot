"""
Logs stuff
"""
import discord
from discord.ext import commands
from .core import trusted, admin, green
from firebase_admin import *
from firebase_admin import firestore

try:
    cred = credentials.Certificate("Config/firebase.json")
    initialize_app(cred)
except ValueError:
    pass
db = firestore.client()
fs_data = db.collection("fun")
settings = db.collection("settings")

logtypes = ["invites"]


def find_invite_by_code(invite_list, code):
    """
    Gets an invite object from its code
    """
    for inv in invite_list:
        if inv.code == code:
            return inv


class log(commands.Cog):
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
    @commands.check(trusted)
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
        if "invites" not in fs_data.document(str(member.guild.id)).get().to_dict():
            return
        invites_before_join = self.invites[member.guild.id]
        invites_after_join = await member.guild.invites()
        for invite in invites_before_join:
            if invite.uses < find_invite_by_code(invites_after_join, invite.code).uses:
                embed = discord.Embed(title="Member joined", description=f"{member.mention}({member.name}) was invited by {invite.inviter.mention}({invite.inviter}) using invite https://discord.gg/{invite.code}")
                await self.bot.get_channel(fs_data.document(str(member.guild.id)).get().to_dict()["invites"]).send(embed=embed)
                self.invites[member.guild.id] = invites_after_join
                return

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """
        Updates list of invites when a user leaves
        """
        for x in await member.guild.invites():
            if x.inviter.id == member.id:
                await x.delete()
        self.invites[member.guild.id] = await member.guild.invites()

    @commands.command()
    @commands.check(admin)
    async def log(self, ctx, t, channel: discord.TextChannel):
        """
        Tells the bot to log something to a channel
        """
        if t not in logtypes:
            raise commands.BadArgument()
        d = fs_data.document(str(ctx.guild.id)).get().to_dict()
        if d is None:
            d = {}
        d[t] = channel.id
        fs_data.document(str(ctx.guild.id)).set(d)
        embed = discord.Embed(title="Log setup", colour=green)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(log(bot))
