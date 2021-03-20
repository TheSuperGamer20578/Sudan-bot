"""
Give info about EMC
"""
import discord
import emc
from emc.async_ import get_data
from discord.ext import commands

from core import RED


BLUE = 0x3357CC


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
            embed.set_author(name=ctx.author.nick, icon_url=ctx.author.avatar_url)
        else:
            embed = discord.Embed(title=town.name, colour=int(town.colour[1:], 16))
            embed.set_author(name=ctx.author.nick, icon_url=ctx.author.avatar_url)
            embed.add_field(name="Mayor", value=f"```{town.mayor}```")
            embed.add_field(name="Nation", value=f"```{town.nation}```")
            embed.add_field(name="Flags", value=f"""```
Capital   : {'🟩' if town.flags['capital'] else '🟥'}
Fire      : {'🟩' if town.flags['fire'] else '🟥'}
Explosions: {'🟩' if town.flags['explosions'] else '🟥'}
Mobs      : {'🟩' if town.flags['mobs'] else '🟥'}
PVP       : {'🟩' if town.flags['pvp'] else '🟥'}
```""")
            residents = ", ".join([res.name for res in town.residents])
            if len(residents) > 1024:
                residents_a = residents[:1024].split(', ')[:-1]
                embed.add_field(name=f"Residents [{len(town.residents)}]:", value=f"```{', '.join(residents_a)}```")
                embed.add_field(name="\N{zero width space}", value=f"```{', '.join([res.name for res in town.residents[-len(residents_a):]])}```")
            else:
                embed.add_field(name=f"Residents [{len(town.residents)}]", value=f"```{residents}```")
            online = [res.name for res in town.residents if res.online]
            embed.add_field(name=f"Online residents [{len(online)}]", value=f"```{', '.join(online)}```")
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(info(bot))
