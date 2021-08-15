"""
Give info about EMC
"""
import discord
import emc
from emc.async_ import get_data
from discord.ext import commands, tasks

from _Util import RED, BLUE, GREEN, Checks


def _long_fields(embed, title, list_):
    all_comma_sep = ", ".join(list_)
    if len(all_comma_sep) > 1024-6:
        list_a = all_comma_sep[:1024-6].split(", ")[:-1]
        embed.add_field(name=title, value=f"```{', '.join(list_a)}```", inline=False)
        _long_fields(embed, "\N{zero width space}", list_[len(list_a):])
    else:
        embed.add_field(name=title, value=f"```{all_comma_sep}```", inline=False)


class Info(commands.Cog):
    """
    Main class
    """
    last_townless = set()

    def __init__(self, bot):
        self.bot = bot
        if bot.is_ready():
            self.update_townless.start()  # pylint: disable=no-member

    @commands.Cog.listener()
    async def on_ready(self):
        """Starts townless updating if bot not ready when cog loaded"""
        self.update_townless.start()  # pylint: disable=no-member

    @commands.command(aliases=["t"])
    @commands.check(Checks.slash)
    async def town(self, ctx, town_to_find):
        """
        Gives info about a town
        """
        await ctx.message.delete()
        try:
            async with ctx.typing():
                town = emc.Town(town_to_find, data=await get_data())
        except emc.exceptions.TownNotFoundException:
            embed = discord.Embed(title=f"The town {town_to_find} was not found", colour=RED)
        else:
            embed = discord.Embed(title=town.name, colour=int(town.colour[1:], 16))
            embed.add_field(name="Mayor", value=f"```{town.mayor}```")
            embed.add_field(name="Nation", value=f"```{town.nation}```")
            embed.add_field(name="Flags", value=f"""```diff
{'+' if town.flags['capital'] else '-'} Capital
{'+' if town.flags['fire'] else '-'} Fire
{'+' if town.flags['explosions'] else '-'} Explosions
{'+' if town.flags['mobs'] else '-'} Mobs
{'+' if town.flags['pvp'] else '-'} PVP
```""")
            _long_fields(embed, f"Residents [{len(town.residents)}]", [res.name for res in town.residents])
            online = [res.name for res in town.residents if res.online]
            if len(online) > 0:
                embed.add_field(name=f"Online residents [{len(online)}]", value=f"```{', '.join(online)}```", inline=False)
            else:
                embed.add_field(name="Online residents [0]", value=f"```No online residents in {town}```", inline=False)
        embed.set_author(name=ctx.author.nick, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["n"])
    @commands.check(Checks.slash)
    async def nation(self, ctx, nation_to_find="Sudan"):
        """Gives info about a nation"""
        await ctx.message.delete()
        try:
            async with ctx.typing():
                nation = emc.Nation(nation_to_find, data=await get_data())
        except emc.exceptions.NationNotFoundException:
            embed = discord.Embed(title=f"The nation {nation_to_find} was not found", colour=RED)
        else:
            embed = discord.Embed(title=nation.name, colour=int(nation.colour[1:], 16))
            embed.add_field(name="Leader", value=f"```{nation.leader}```")
            embed.add_field(name="Capital", value=f"```{nation.capital}```")
            embed.add_field(name="Population", value=f"```{len(nation.citizens)}```")
            _long_fields(embed, f"Towns [{len(nation.towns)}]", [town.name for town in nation.towns])
            online = [res.name for res in nation.citizens if res.online]
            if len(online) > 0:
                embed.add_field(name=f"Online [{len(online)}]", value=f"```{', '.join(online)}```", inline=False)
            else:
                embed.add_field(name="Online [0]", value=f"```0 citizens online in {nation}```", inline=False)
        embed.set_author(name=ctx.author.nick, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["res", "player", "pl"])
    @commands.check(Checks.slash)
    async def resident(self, ctx, resident_to_find):
        """Gives info about a player"""
        await ctx.message.delete()
        async with ctx.typing():
            resident = emc.Resident(resident_to_find, data=await get_data())
        embed = discord.Embed(title=resident.name, colour=BLUE)
        embed.set_thumbnail(url=f"https://minotar.net/armor/bust/{resident}")
        embed.add_field(name="Town", value=f"```{resident.town}```")
        embed.add_field(name="Nation", value=f"```{resident.nation}```")
        if resident.online:
            if resident.hidden:
                embed.add_field(name="Position", value=f"```{resident} is currently not visable on the map```")
            else:
                embed.add_field(name="Position", value=f"```{resident.position[0]}/{resident.position[1]}/{resident.position[2]}```([map]({emc.util.map_link(resident.position)}))")
        else:
            embed.add_field(name="Position", value=f"```{resident} is currently offline```")
        embed.set_author(name=ctx.author.nick, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.check(Checks.admin)
    async def townless(self, ctx, channel: discord.TextChannel = None):
        """Sends a message in the specified channel with all the townless people on it, updates automatically"""
        await ctx.message.delete()
        if channel is not None:
            townless = self.last_townless
            townless_display = "\n".join(townless)
            if len(townless) == 0:
                townless_display = "There are currently no townless players :("
            embed = discord.Embed(title=f"Townless players [{len(townless)}]", description=f"```\n{townless_display}```", colour=BLUE)
            message = await channel.send(embed=embed)
            async with self.bot.pool.acquire() as db:
                await db.execute("UPDATE guilds SET townless_channel = $2, townless_message = $3 WHERE id = $1", ctx.guild.id, channel.id, message.id)
            embed = discord.Embed(title=f"Set townless channel to #{channel.name}", colour=GREEN)
        else:
            async with self.bot.pool.acquire() as db:
                await db.execute("UPDATE guilds SET townless_channel = NULL, townless_message = NULL WHERE id = $1", ctx.guild.id)
            embed = discord.Embed(title="Disabled townless", colour=GREEN)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @tasks.loop(seconds=5)
    async def update_townless(self):
        """Automatically update townless stuff"""
        townless = {resident.name for resident in emc.Resident.all_online(data=await get_data()) if resident.town is None}
        if townless != self.last_townless:
            self.last_townless = townless
            townless_display = "\n".join(townless)
            if len(townless) == 0:
                townless_display = "There are currently no townless players :("
            embed = discord.Embed(title=f"Townless players [{len(townless)}]", description=f"```\n{townless_display}```", colour=BLUE)
            async with self.bot.pool.acquire() as db:
                for message in await db.fetch("SELECT id, townless_channel, townless_message FROM guilds WHERE townless_message IS NOT NULL"):
                    channel = self.bot.get_guild(message["id"]).get_channel(message["townless_channel"])
                    message = await channel.fetch_message(message["townless_message"])
                    await message.edit(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(Info(bot))
