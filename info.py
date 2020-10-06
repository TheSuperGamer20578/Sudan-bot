"""
Give info about EMC
STILL A WORK IN PROGRESS
"""
import queue
import threading
import discord
# import sys
# import time
from discord.ext import commands, tasks
from core import RED

# sys.path.insert(1, "E:\\Python\\EMC-info\\code\\EMC-info\\src")
import EMC

BLUE = 0x3357CC
DATA = None
que = queue.Queue()


class info(commands.Cog):
    """
    Main class
    """
    def __init__(self, bot):
        self.bot = bot
        self.update_data.start()

    @tasks.loop(seconds=10)
    async def update_data(self):
        """
        Updates the data every 10 secs
        """
        global DATA
        thread = threading.Thread(target=lambda q: q.put(EMC.get_data()), args=(que,))
        thread.start()
        DATA = que.get()

    @commands.command(aliases=["t"])
    async def town(self, ctx, town_to_find):
        """
        Gives info about a town
        """
        await ctx.message.delete()
        try:
            town = EMC.Town(town_to_find, DATA)
        except EMC.TownNotFound:
            embed = discord.Embed(title=f"The town {town_to_find} was not found", colour=RED)
            embed.set_author(name=ctx.author.nick, icon_url=ctx.author.avatar_url)
        else:
            embed = discord.Embed(title=town.name, colour=BLUE)
            embed.set_author(name=ctx.author.nick, icon_url=ctx.author.avatar_url)
            embed.add_field(name="Mayor", value=f"```{town.mayor.name}```")
            if not town.nationless:
                embed.add_field(name="Nation", value=f"```{town.nation.name}```")
            embed.add_field(name="Flags", value=f"""```
Capital   : {'🟩' if town.capital else '🟥'}
Fire      : {'🟩' if town.fire else '🟥'}
Explosions: {'🟩' if town.explosions else '🟥'}
Nationless: {'🟩' if town.nationless else '🟥'}
Mobs      : {'🟩' if town.mobSpawns else '🟥'}
PVP       : {'🟩' if town.pvp else '🟥'}
```""")
            residents = ""
            online_residents = ""
            for resident in town.residents:
                residents += f"{resident.name}, "
                online_residents += f"{resident.name}, " if resident.online else ""
            residents = residents[:-2]
            online_residents = online_residents[:-2] if len(online_residents) > 2 else f"No online residents in {town.name}"
            if len(residents) <= 1017:
                embed.add_field(name=f"Residents [{len(town.residents)}]", value=f"```{residents}```", inline=False)
            else:
                res_a = ", ".join(residents[:1016].split(", ")[:-1]) + ","
                res_b = residents[len(residents[:1016])+len(residents[:1016].split(", ")[-1])+2:]
                embed.add_field(name=f"Residents [{len(town.residents)}]", value=f"```{res_a}```", inline=False)
                embed.add_field(name="\N{zero width space}", value=f"```{res_b}```", inline=False)
            embed.add_field(name=f"Online residents[{len([resident for resident in town.residents if x.online])}]", value=f"```{online_residents}```",
                            inline=False)
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(info(bot))
