"""
Makes a rule embed will be used to set punishments when moderation is added
"""
import discord
from discord.ext import commands

from _Util import BLUE, Checks


class Rules(commands.Cog):
    """
    Main class
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @commands.check(Checks.admin)
    async def rules(self, ctx):
        """
        Modifies rules
        """

    @rules.command(aliases=["add", "create"])
    @commands.check(Checks.admin)
    async def set(self, ctx, name, punishment, *, description):
        """
        makes a rule
        """
        await self.bot.db.execute("INSERT INTO rules (name, guild_id, punishment, description) VALUES ($2, $1, $3, $4)",
                                  ctx.guild.id, name, punishment, description)
        await ctx.message.delete()
        embed = discord.Embed(title="Rules updated")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @rules.command(aliases=["del", "remove"])
    @commands.check(Checks.admin)
    async def delete(self, ctx, name):
        """
        deletes a rule
        """
        await self.bot.db.execute("DELETE FROM rules WHERE guild_id = $1 AND name = $2",
                                  ctx.guild.id, name)
        await ctx.message.delete()
        embed = discord.Embed(title="Rules updated")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @rules.command()
    @commands.check(Checks.admin)
    async def clear(self, ctx):
        """
        clears all rules
        """
        await self.bot.db.execute("DELETE FROM rules WHERE guild_id = $1", ctx.guild.id)
        await ctx.message.delete()
        embed = discord.Embed(title="Rules updated")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.check(Checks.admin)
    async def sendrules(self, ctx, channel: discord.TextChannel, inline: bool = False):
        """
        Sends rules to the specified channel
        """
        punishments = [punishment["punishment"] for punishment in await self.bot.db.fetch("SELECT DISTINCT punishment FROM rules WHERE guild_id = $1 AND punishment != 'faq'", ctx.guild.id)]
        embed = discord.Embed(title="Rules")
        for punishment in punishments:
            embed.add_field(name=punishment, value="\n\n".join([rule["description"] for rule in await self.bot.db.fetch("SELECT description FROM rules WHERE guild_id = $1 AND punishment = $2", ctx.guild.id, punishment)]), inline=inline)
        for faq in [(faq["name"], faq["description"]) for faq in await self.bot.db.fetch("SELECT name, description FROM rules WHERE guild_id = $1 AND punishment = 'faq'", ctx.guild.id)]:
            embed.add_field(name=faq[0], value=faq[1], inline=inline)
        await ctx.message.delete()
        await channel.send(embed=embed)
        embed = discord.Embed(title=f"Rules sent to #{channel.name}")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def rule(self, ctx, name):
        """
        Shows info of a rule
        """
        rule = await self.bot.db.fetchrow("SELECT name, punishment, description FROM rules WHERE guild_id = $1 AND name = $2 AND punishment != 'faq'",
                                          ctx.guild.id, name)
        embed = discord.Embed(title=name, description=rule["description"], colour=BLUE)
        embed.add_field(name="Punishment:", value=rule["punishment"])
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(Rules(bot))
