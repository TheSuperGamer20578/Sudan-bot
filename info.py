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

# sys.path.insert(1, "E:\\Python\\EMC-info\\code\\EMC-info\\src")
import EMC

BLUE = 0x3357CC
red = 0xb00e0e
data = None
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
        global data
        thread = threading.Thread(target=lambda q: q.put(EMC.get_data()), args=(que,))
        thread.start()
        data = que.get()

    @commands.command(aliases=["t"])
    async def town(self, ctx, town):
        """
        Gives info about a town
        """
        await ctx.message.delete()
        try:
            t = EMC.Town(town, data)
        except EMC.TownNotFound:
            embed = discord.Embed(title=f"The town {town} was not found", colour=RED)
            embed.set_author(name=ctx.author.nick, icon_url=ctx.author.avatar_url)
        else:
            embed = discord.Embed(title=t.name, colour=BLUE)
            embed.set_author(name=ctx.author.nick, icon_url=ctx.author.avatar_url)
            embed.add_field(name="Mayor", value=f"```{t.mayor.name}```")
            if not t.nationless:
                embed.add_field(name="Nation", value=f"```{t.nation.name}```")
            embed.add_field(name="Flags", value=f"""```
Capital   : {'🟩' if t.capital else '🟥'}
Fire      : {'🟩' if t.fire else '🟥'}
Explosions: {'🟩' if t.explosions else '🟥'}
Nationless: {'🟩' if t.nationless else '🟥'}
Mobs      : {'🟩' if t.mobSpawns else '🟥'}
PVP       : {'🟩' if t.pvp else '🟥'}
```""")
            r = ""
            o = ""
            for x in t.residents:
                r += f"{x.name}, "
                o += f"{x.name}, " if x.online else ""
            r = r[:-2]
            o = o[:-2] if len(o) > 2 else f"No online residents in {t.name}"
            if len(r) <= 1017:
                embed.add_field(name=f"Residents [{len(t.residents)}]", value=f"```{r}```", inline=False)
            else:
                a = ", ".join(r[:1016].split(", ")[:-1]) + ","
                b = r[len(r[:1016])+len(r[:1016].split(", ")[-1])+2:]
                embed.add_field(name=f"Residents [{len(t.residents)}]", value=f"```{a}```", inline=False)
                embed.add_field(name="\N{zero width space}", value=f"```{b}```", inline=False)
            embed.add_field(name=f"Online residents[{len([x for x in t.residents if x.online])}]", value=f"```{o}```",
                            inline=False)
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(info(bot))
