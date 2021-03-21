"""
Give info about EMC
"""
import discord
import emc
from emc.async_ import get_data
from discord.ext import commands

from core import RED


BLUE = 0x3357CC


def _long_fields(embed, title, list_):
    all_comma_sep = ", ".join(list_)
    if len(all_comma_sep) > 1024-6:
        list_a = all_comma_sep[:1024-6].split(', ')[:-1]
        embed.add_field(name=title, value=f"```{', '.join(list_a)}```", inline=False)
        _long_fields(embed, "\N{zero width space}", list_[len(list_a):])
    else:
        embed.add_field(name=title, value=f"```{all_comma_sep}```", inline=False)



class info(commands.Cog):
    """
    Main class
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["t"])
    async def town(self, ctx, town_to_find):
        """
        Gives info about a town
        """
        await ctx.message.delete()
        try:
            town = emc.Town(town_to_find, data=await get_data())
        except emc.exceptions.TownNotFoundException:
            embed = discord.Embed(title=f"The town {town_to_find} was not found", colour=RED)
        else:
            embed = discord.Embed(title=town.name, colour=int(town.colour[1:], 16))
            embed.add_field(name="Mayor", value=f"```{town.mayor}```")
            embed.add_field(name="Nation", value=f"```{town.nation}```")
            embed.add_field(name="Flags", value=f"""```
Capital   : {'🟩' if town.flags['capital'] else '🟥'}
Fire      : {'🟩' if town.flags['fire'] else '🟥'}
Explosions: {'🟩' if town.flags['explosions'] else '🟥'}
Mobs      : {'🟩' if town.flags['mobs'] else '🟥'}
PVP       : {'🟩' if town.flags['pvp'] else '🟥'}
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
    async def nation(self, ctx, nation_to_find="Sudan"):
        """Gives info about a nation"""
        await ctx.message.delete()
        try:
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


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(info(bot))
