"""
Logs stuff
"""
import discord
from discord.ext import commands
from firebase_admin import firestore, credentials, initialize_app

from core import trusted, admin, GREEN

try:
    cred = credentials.Certificate("Config/firebase.json")
    initialize_app(cred)
except ValueError:
    pass
db = firestore.client()
fs_data = db.collection("logging")

logtypes = ["invites"]


def find_invite_by_code(invite_list, code):
    """
    Gets an invite object from its code
    """
    for inv in invite_list:
        if inv.code == code:
            return inv
    return None


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
        for invites in await member.guild.invites():
            if invites.inviter.id == member.id:
                await invites.delete()
        self.invites[member.guild.id] = await member.guild.invites()

    @commands.command()
    @commands.check(admin)
    async def log(self, ctx, log_type, channel: discord.TextChannel):
        """
        Tells the bot to log something to a channel
        """
        if log_type not in logtypes:
            raise commands.BadArgument()
        data = fs_data.document(str(ctx.guild.id)).get().to_dict()
        if data is None:
            data = {}
        data[log_type] = channel.id
        fs_data.document(str(ctx.guild.id)).set(data)
        embed = discord.Embed(title="Log setup", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(log(bot))
