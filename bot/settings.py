"""
A global config for the bot
"""
import discord
from discord.ext import commands

from _util import GREEN, Checks

settable = {
    "mod_roles": list,
    "admin_roles": list,
    "support_role": int,
    "chain_break_role": int
}


class settings(commands.Cog):
    """
    Main class
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=False, aliases=["set"])
    async def settings(self, ctx):
        embed = discord.Embed(title="Settings")
        if Checks.admin(ctx):
            settings = await self.bot.db.fetchrow("SELECT * FROM guilds WHERE id = $1", ctx.guild.id)
            embed.add_field(name="Server settings", inline=False, value=f"""
                Admin roles: {', '.join([f'<@&{role}>' for role in settings["admin_roles"]])}
                Moderator roles: {', '.join([f'<@&{role}>' for role in settings["mod_roles"]])}
                Ticket support role: {f'<@&{settings["support_role"]}>'}
                Chain break role: {f'<@&{settings["chain_break_role"]}>'}
            """)
        settings = await self.bot.db.fetchrow("SELECT * FROM users WHERE id = $1", ctx.author.id)
        embed.add_field(name="User settings", inline=False, value=f"""
            Dad mode: {'🟢' if settings['dad_mode'] else '🔴'}
        """)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(settings(bot))
