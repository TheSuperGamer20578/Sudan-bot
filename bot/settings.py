"""
A global config for the bot
"""
import discord
from discord.ext import commands

from _util import GREEN, BLUE, Checks


class settings(commands.Cog):
    """
    Main class
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=False, aliases=["set"])
    async def settings(self, ctx):
        await ctx.message.delete()
        embed = discord.Embed(title="Settings", colour=BLUE)
        if Checks.admin(ctx):
            settings = await self.bot.db.fetchrow("SELECT * FROM guilds WHERE id = $1", ctx.guild.id)
            embed.add_field(name="Server settings", inline=False, value=f"""
                Admin roles: {', '.join([f'<@&{role}>' for role in settings["admin_roles"]])}
                Moderator roles: {', '.join([f'<@&{role}>' for role in settings["mod_roles"]])}
                Ticket support roles: {', '.join([f'<@&{role}>' for role in settings["mod_roles"]])}
                Chain break role: {f'<@&{settings["chain_break_role"]}>'}
            """)
        settings = await self.bot.db.fetchrow("SELECT * FROM users WHERE id = $1", ctx.author.id)
        embed.add_field(name="User settings", inline=False, value=f"""
            Dad mode: {'🟢' if settings['dad_mode'] else '🔴'}
        """)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @settings.group(invoke_without_command=False)
    @commands.check(Checks.admin)
    async def admin(self, ctx):
        settings = await self.bot.db.fetchrow("SELECT * FROM guilds WHERE id = $1", ctx.guild.id)
        await ctx.message.delete()
        embed = discord.Embed(title="Admin roles", colour=BLUE, description=", ".join([f'<@&{role}>' for role in settings["admin_roles"]]))
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @admin.command(name="add")
    @commands.check(lambda ctx: Checks.admin(ctx) or ctx.author == ctx.guild.owner)
    async def admin_add(self, ctx, role: discord.Role):
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET admin_roles = ARRAY_APPEND(admin_roles, $2) WHERE id = $1", ctx.guild.id, role.id)
        embed = discord.Embed(title=f"Added {role.mention} to admin roles", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @admin.command(name="remove")
    @commands.check(Checks.admin)
    async def admin_remove(self, ctx, role: discord.Role):
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET admin_roles = ARRAY_REMOVE(admin_roles, $2) WHERE id = $1", ctx.guild.id, role.id)
        embed = discord.Embed(title=f"Removed {role.mention} from admin roles", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @settings.group(invoke_without_command=False)
    @commands.check(Checks.admin)
    async def mod(self, ctx):
        settings = await self.bot.db.fetchrow("SELECT * FROM guilds WHERE id = $1", ctx.guild.id)
        await ctx.message.delete()
        embed = discord.Embed(title="Moderator roles", colour=BLUE, description=", ".join([f'<@&{role}>' for role in settings["mod_roles"]]))
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @mod.command(name="add")
    @commands.check(Checks.admin)
    async def mod_add(self, ctx, role: discord.Role):
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET mod_roles = ARRAY_APPEND(mod_roles, $2) WHERE id = $1", ctx.guild.id, role.id)
        embed = discord.Embed(title=f"Added {role.mention} to moderator roles", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @mod.command(name="remove")
    @commands.check(Checks.admin)
    async def mod_remove(self, ctx, role: discord.Role):
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET mod_roles = ARRAY_REMOVE(mod_roles, $2) WHERE id = $1", ctx.guild.id, role.id)
        embed = discord.Embed(title=f"Removed {role.mention} from moderator roles", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @settings.group(invoke_without_command=False)
    @commands.check(Checks.admin)
    async def support(self, ctx):
        settings = await self.bot.db.fetchrow("SELECT * FROM guilds WHERE id = $1", ctx.guild.id)
        await ctx.message.delete()
        embed = discord.Embed(title="Ticket support roles", colour=BLUE, description=", ".join([f'<@&{role}>' for role in settings["support_roles"]]))
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @support.command(name="add")
    @commands.check(Checks.admin)
    async def support_add(self, ctx, role: discord.Role):
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET support_roles = ARRAY_APPEND(support_roles, $2) WHERE id = $1", ctx.guild.id, role.id)
        embed = discord.Embed(title=f"Added {role.mention} to ticket support roles", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @support.command(name="remove")
    @commands.check(Checks.admin)
    async def support_remove(self, ctx, role: discord.Role):
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET support_roles = ARRAY_REMOVE(support_roles, $2) WHERE id = $1", ctx.guild.id, role.id)
        embed = discord.Embed(title=f"Removed {role.mention} from ticket support roles", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @settings.command()
    @commands.check(Checks.admin)
    async def breakrole(self, ctx, role: discord.Role):
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET chain_break_role = $2 WHERE id = $1", ctx.guild.id, role.id)
        embed = discord.Embed(title=f"Set chain break role to {role.mention}", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @settings.command()
    async def dad(self, ctx, toggle: bool):
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE users SET dad_mode = $2 WHERE id = $1", ctx.author.id, toggle)
        embed = discord.Embed(title=f"{'Enabled' if toggle else 'Disabled'} dad mode", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(settings(bot))
