"""
A global config for the bot
"""
import discord
from discord.ext import commands

from _Util import GREEN, BLUE, RED, Checks
from moderation import parse_time, human_delta


class Settings(commands.Cog):
    """
    Main class
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, aliases=["set"])
    @commands.check(Checks.slash)
    async def settings(self, ctx):
        """Lists settings"""
        await ctx.message.delete()
        embed = discord.Embed(title="Settings", colour=BLUE)
        if await Checks.admin(ctx):
            settings_ = await self.bot.db.fetchrow("SELECT * FROM guilds WHERE id = $1", ctx.guild.id)
            embed.add_field(name="Server settings", inline=False, value=f"""
                Admin roles: {', '.join([f'<@&{role}>' for role in settings_["admin_roles"]]) if len(settings_['admin_roles']) > 0 else 'None'}
                Moderator roles: {', '.join([f'<@&{role}>' for role in settings_["mod_roles"]]) if len(settings_['mod_roles']) > 0 else 'None'}
                Ticket support roles: {', '.join([f'<@&{role}>' for role in settings_["support_roles"]]) if len(settings_['support_roles']) > 0 else 'None'}
                Chain break role: {f'<@&{settings_["chain_break_role"]}>' if settings_["chain_break_role"] is not None else 'None'}
                Mute role: {f'<@&{settings_["mute_role"]}>' if settings_["mute_role"] is not None else 'None'}
                Private commands: {'🟢' if settings_['private_commands'] else '🔴'}
                Force slash commands: {'🟢' if settings_['force_slash'] else '🔴'}
                Mute threshold: {settings_["mute_threshold"] if settings_["mute_threshold"] != 0 else 'Disabled'}
                Ban threshold: {settings_["ban_threshold"] if settings_["ban_threshold"] != 0 else 'Disabled'}
                Bad words: {', '.join([f'||{word}||' for word in settings_["bad_words"]]) if len(settings_["bad_words"]) > 0 else 'None'}
                Bad words warn duration: {human_delta(settings_["bad_words_warn_duration"])}
            """)
        settings_ = await self.bot.db.fetchrow("SELECT * FROM users WHERE id = $1", ctx.author.id)
        embed.add_field(name="User settings", inline=False, value=f"""
            Dad mode: {'🟢' if settings_['dad_mode'] else '🔴'}
        """)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @settings.group(invoke_without_command=True)
    @commands.check(Checks.admin)
    @commands.check(Checks.slash)
    async def admin(self, ctx):
        """Lists admin roles"""
        roles = await self.bot.db.fetchval("SELECT admin_roles FROM guilds WHERE id = $1", ctx.guild.id)
        await ctx.message.delete()
        embed = discord.Embed(title="Admin roles", colour=BLUE, description=", ".join([f"<@&{role}>" for role in roles]) if len(roles) > 0 else "None")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @admin.command(name="set")
    @commands.check(lambda ctx: ctx.author == ctx.guild.owner)
    @commands.check(Checks.slash)
    async def admin_set(self, ctx, role: discord.Role):
        """Sets the server's admin role"""
        await ctx.message.delete()
        roles = await self.bot.db.fetchval("SELECT admin_roles FROM guilds WHERE id = $1", ctx.guild.id)
        if len(roles) > 0:
            embed = discord.Embed(title="You already have an admin role set", description="use `.set admin add <role>` to add more", colour=RED)
        else:
            await self.bot.db.execute("UPDATE guilds SET admin_roles = ARRAY_APPEND(admin_roles, $2) WHERE id = $1", ctx.guild.id, role.id)
            embed = discord.Embed(title="Settings updated", description=f"Set {role.mention} as this server's admin role", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @admin.command(name="add")
    @commands.check(Checks.admin)
    @commands.check(Checks.slash)
    async def admin_add(self, ctx, role: discord.Role):
        """Adds an admin role"""
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET admin_roles = ARRAY_APPEND(admin_roles, $2) WHERE id = $1", ctx.guild.id, role.id)
        embed = discord.Embed(title="Settings updated", description=f"Added {role.mention} to admin roles", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @admin.command(name="remove")
    @commands.check(Checks.admin)
    @commands.check(Checks.slash)
    async def admin_remove(self, ctx, role: discord.Role):
        """Removes an admin role"""
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET admin_roles = ARRAY_REMOVE(admin_roles, $2) WHERE id = $1", ctx.guild.id, role.id)
        embed = discord.Embed(title="Settings updated", description=f"Removed {role.mention} from admin roles", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @settings.group(invoke_without_command=True)
    @commands.check(Checks.admin)
    @commands.check(Checks.slash)
    async def badwords(self, ctx):
        """Lists bad words"""
        words = await self.bot.db.fetchval("SELECT bad_words FROM guilds WHERE id = $1", ctx.guild.id)
        await ctx.message.delete()
        embed = discord.Embed(title="Bad words", colour=BLUE, description=', '.join([f'||{word}||' for word in words]) if len(words) > 0 else 'None')
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @badwords.command(name="add")
    @commands.check(Checks.admin)
    @commands.check(Checks.slash)
    async def badwords_add(self, ctx, word: str):
        """Adds a bad word"""
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET bad_words = ARRAY_APPEND(bad_words, $2) WHERE id = $1", ctx.guild.id, word)
        embed = discord.Embed(title="Settings updated", description=f"Added ||{word}|| to bad words", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @badwords.command(name="remove")
    @commands.check(Checks.admin)
    @commands.check(Checks.slash)
    async def badwords_remove(self, ctx, word: str):
        """Removes a bad word"""
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET bad_words = ARRAY_REMOVE(bad_words, $2) WHERE id = $1", ctx.guild.id, word)
        embed = discord.Embed(title="Settings updated", description=f"Removed ||{word}|| from bad words", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @settings.group(invoke_without_command=True)
    @commands.check(Checks.admin)
    @commands.check(Checks.slash)
    async def mod(self, ctx):
        """Lists moderator roles"""
        roles = await self.bot.db.fetchval("SELECT mod_roles FROM guilds WHERE id = $1", ctx.guild.id)
        await ctx.message.delete()
        embed = discord.Embed(title="Moderator roles", colour=BLUE, description=", ".join([f"<@&{role}>" for role in roles]) if len(roles) > 0 else "None")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @mod.command(name="add")
    @commands.check(Checks.admin)
    @commands.check(Checks.slash)
    async def mod_add(self, ctx, role: discord.Role):
        """Adds moderator role"""
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET mod_roles = ARRAY_APPEND(mod_roles, $2) WHERE id = $1", ctx.guild.id, role.id)
        embed = discord.Embed(title="Settings updated", description=f"Added {role.mention} to moderator roles", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @mod.command(name="remove")
    @commands.check(Checks.admin)
    @commands.check(Checks.slash)
    async def mod_remove(self, ctx, role: discord.Role):
        """Removes moderator role"""
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET mod_roles = ARRAY_REMOVE(mod_roles, $2) WHERE id = $1", ctx.guild.id, role.id)
        embed = discord.Embed(title="Settings updated", description=f"Removed {role.mention} from moderator roles", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @settings.group(invoke_without_command=True)
    @commands.check(Checks.admin)
    @commands.check(Checks.slash)
    async def support(self, ctx):
        """Lists ticket support roles"""
        roles = await self.bot.db.fetchval("SELECT support_roles FROM guilds WHERE id = $1", ctx.guild.id)
        await ctx.message.delete()
        embed = discord.Embed(title="Ticket support roles", colour=BLUE, description=", ".join([f"<@&{role}>" for role in roles]) if len(roles) > 0 else "None")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @support.command(name="add")
    @commands.check(Checks.admin)
    @commands.check(Checks.slash)
    async def support_add(self, ctx, role: discord.Role):
        """Adds ticket support role"""
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET support_roles = ARRAY_APPEND(support_roles, $2) WHERE id = $1", ctx.guild.id, role.id)
        embed = discord.Embed(title="Settings updated", description=f"Added {role.mention} to ticket support roles", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @support.command(name="remove")
    @commands.check(Checks.admin)
    @commands.check(Checks.slash)
    async def support_remove(self, ctx, role: discord.Role):
        """Removes ticket support role"""
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET support_roles = ARRAY_REMOVE(support_roles, $2) WHERE id = $1", ctx.guild.id, role.id)
        embed = discord.Embed(title="Settings updated", description=f"Removed {role.mention} from ticket support roles", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @settings.command()
    @commands.check(Checks.admin)
    @commands.check(Checks.slash)
    async def breakrole(self, ctx, role: discord.Role):
        """Sets the chain break role"""
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET chain_break_role = $2 WHERE id = $1", ctx.guild.id, role.id)
        embed = discord.Embed(title="Settings updated", description=f"Set chain break role to {role.mention}", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @settings.command()
    @commands.check(Checks.admin)
    @commands.check(Checks.slash)
    async def muterole(self, ctx, role: discord.Role):
        """Sets the mute role"""
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET mute_role = $2 WHERE id = $1", ctx.guild.id, role.id)
        embed = discord.Embed(title="Settings updated", description=f"Set mute role to {role.mention}", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @settings.command()
    @commands.check(Checks.admin)
    @commands.check(Checks.slash)
    async def private(self, ctx, toggle: bool):
        """Enables or disables private commands"""
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET private_commands = $2 WHERE id = $1", ctx.guild.id, toggle)
        embed = discord.Embed(title="Settings updated", description=f"{'Enabled' if toggle else 'Disabled'} private commands", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @settings.command()
    @commands.check(Checks.admin)
    @commands.check(Checks.slash)
    async def forceslash(self, ctx, toggle: bool):
        """Enables or disables forced slash command usage"""
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET force_slash = $2 WHERE id = $1", ctx.guild.id, toggle)
        embed = discord.Embed(title="Settings updated", description=f"{'Enabled' if toggle else 'Disabled'} forced slash commands", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @settings.command()
    @commands.check(Checks.admin)
    @commands.check(Checks.slash)
    async def mutethreshold(self, ctx, threshold: int):
        """Set how many warns a member can have before being muted"""
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET mute_threshold = $2 WHERE id = $1", ctx.guild.id, threshold)
        embed = discord.Embed(title="Settings updated", description=f"Set mute threshold to {threshold}", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @settings.command()
    @commands.check(Checks.admin)
    @commands.check(Checks.slash)
    async def banthreshold(self, ctx, threshold: int):
        """Set how many warns a member can have before being banned"""
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET ban_threshold = $2 WHERE id = $1", ctx.guild.id, threshold)
        embed = discord.Embed(title="Settings updated", description=f"Set ban threshold to {threshold}", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @settings.command()
    @commands.check(Checks.admin)
    async def badwordswarn(self, ctx, duration: commands.Greedy[parse_time]):
        """Sets how long the warning for saying a bad word should last"""
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE guilds SET bad_words_warn_duration = $2 WHERE id = $1", ctx.guild.id, sum(duration))
        embed = discord.Embed(title="Settings updated", description=f"Set bad words warn duration to {human_delta(sum(duration))}", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @settings.command()
    @commands.check(Checks.slash)
    async def dad(self, ctx, toggle: bool):
        """Enables or disables dad mode"""
        await ctx.message.delete()
        await self.bot.db.execute("UPDATE users SET dad_mode = $2 WHERE id = $1", ctx.author.id, toggle)
        embed = discord.Embed(title="Settings updated", description=f"{'Enabled' if toggle else 'Disabled'} dad mode", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(Settings(bot))
