import json
import threading
import asyncio
import discord
import EMC
from discord.ext import commands

with open("Config/attack.json", "r") as f:
    d = json.loads(f.read())
    enemys = d["enemys"]
    borders = d["borders"]


class attack(commands.Cog):
    def __init__(self, bot):
        self.i = {}
        self.bot = bot
        self.thread = threading.Thread(target=asyncio.run, args=(self.loop(),))

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.get_channel(731402228820213882).purge(limit=1000000)
        for x in borders:
            embed = discord.Embed(title=f"0 Enemy/s near {x}")
            borders[x]["msg"] = await self.bot.get_channel(731402228820213882).send(embed=embed)
            self.i[x] = []
        self.thread.start()

    @commands.is_owner()
    @commands.command()
    async def attackstart(self, ctx):
        await self.bot.get_channel(731402228820213882).purge(limit=1000000)
        for x in borders:
            embed = discord.Embed(title=f"0 Enemy/s near {x}")
            borders[x]["msg"] = await self.bot.get_channel(731402228820213882).send(embed=embed)
            self.i[x] = []
        self.thread.start()

    @commands.is_owner()
    @commands.command()
    async def updateattack(self, ctx):
        with open("Config/attack.json", "r") as f:
            d = json.loads(f.read())
            enemys = d["enemys"]
            borders = d["borders"]

    async def loop(self):
        data = await EMC.a_get_data()

        def c(self, r):
            for x in borders:
                try:
                    if r.pos == (0.0, 64.0, 0.0):
                        pass
                    elif borders[x]["top"] <= r.pos[2] <= borders[x]["bottom"] and borders[x]["left"] <= r.pos[0] <= \
                            borders[x]["right"]:
                        if r.name not in self.i[x]:
                            self.i[x].append(r.name)
                    elif r.name in self.i[x]:
                        self.i[x].remove(r.name)
                except AttributeError:
                    if r.name in self.i[x]:
                        self.i[x].remove(r.name)

        try:
            for x in enemys["players"]:
                c(self, EMC.Resident(x, data))
            for x in enemys["towns"]:
                for y in EMC.Town(x, data).residents:
                    c(self, y)
            for x in enemys["nations"]:
                for y in EMC.Nation(x, data).residents:
                    c(self, y)
        except TypeError:
            print(TypeError)
        for x in self.i:
            msg = ""
            for y in self.i[x]:
                r = EMC.Resident(y, data)
                if r.pos == (0.0, 64.0, 0.0):
                    msg += f"[{r.town.nation.name} | {r.town.name}] {r.name} (UNKNOWN)\n"
                else:
                    msg += f"[{r.town.nation.name} | {r.town.name}] {r.name} [{r.pos}](https://earthmc.net/map/?worldname=earth&mapname=flat&zoom=8&x={r.pos[0]}&y={r.pos[1]}&z={r.pos[2]})\n"
            embed = discord.Embed(title=f"{len(self.i[x])} enemy/s near {x}", description=msg)
            await borders[x]["msg"].edit(embed=embed)
            if len(self.i[x]) > 0:
                await self.bot.get_channel(731402228820213882).send(f"<@&{borders[x]['id']}>", tts=True, delete_after=0)
        return await self.loop()


def setup(bot):
    bot.add_cog(attack(bot))
