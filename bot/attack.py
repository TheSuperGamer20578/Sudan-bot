"""
Only works in a singular server and may be unstable
"""
# TODO remove this comment and the one below
# pylint: skip-file
import json
import threading
import asyncio

import discord
import EMC
from discord.ext import commands

with open("Config/attack.json", "r") as file:
    DATA = json.loads(file.read())
    enemys = DATA["enemys"]
    borders = DATA["borders"]


class attack(commands.Cog):
    """
    Alerts when an enemy is within a set area
    """
    def __init__(self, bot):
        self.invading = {}
        self.bot = bot
        self.thread = threading.Thread(target=asyncio.run, args=(self.loop(),))

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Send initial messages and set variable
        """
        await self.bot.get_channel(731402228820213882).purge(limit=1000000)
        for border in borders:
            embed = discord.Embed(title=f"0 Enemy/s near {border}")
            borders[border]["msg"] = await self.bot.get_channel(731402228820213882).send(embed=embed)
            self.invading[border] = []
        self.thread.start()

    @commands.is_owner()
    @commands.command(pass_context=False)
    async def attackstart(self):
        """
        Same as on_ready but for when cog is loaded after startup
        """
        await self.bot.get_channel(731402228820213882).purge(limit=1000000)
        for border in borders:
            embed = discord.Embed(title=f"0 Enemy/s near {border}")
            borders[border]["msg"] = await self.bot.get_channel(731402228820213882).send(embed=embed)
            self.invading[border] = []
        self.thread.start()

    @commands.is_owner()
    @commands.command(pass_context=False)
    async def updateattack(self):
        """
        Supposed to reload config for this cog
        """
        with open("Config/attack.json", "r") as file:
            data = json.loads(file.read())
            enemys = data["enemys"]
            borders = data["borders"]

    async def loop(self):
        """
        Runs regularly to check if enemies are in set area
        """
        data = await EMC.a_get_data()

        def invader_check(self, resident):
            """
            Actually do the check
            """
            for border in borders:
                try:
                    if resident.pos == (0.0, 64.0, 0.0):
                        pass
                    elif borders[border]["top"] <= resident.pos[2] <= borders[border]["bottom"] and borders[border]["left"] <= resident.pos[0] <= \
                            borders[border]["right"]:
                        if resident.name not in self.invading[border]:
                            self.invading[border].append(resident.name)
                    elif resident.name in self.invading[border]:
                        self.invading[border].remove(resident.name)
                except AttributeError:
                    if resident.name in self.invading[border]:
                        self.invading[border].remove(resident.name)

        try:
            for enemy in enemys["players"]:
                invader_check(self, EMC.Resident(enemy, data))
            for enemy in enemys["towns"]:
                for resident in EMC.Town(enemy, data).residents:
                    invader_check(self, resident)
            for enemy in enemys["nations"]:
                for resident in EMC.Nation(enemy, data).residents:
                    invader_check(self, resident)
        except TypeError:
            print(TypeError)
        for enemy in self.invading:
            msg = ""
            for resident in self.invading[enemy]:
                resident = EMC.Resident(resident, data)
                if resident.pos == (0.0, 64.0, 0.0):
                    msg += f"[{resident.town.nation.name} | {resident.town.name}] {resident.name} (UNKNOWN)\n"
                else:
                    msg += f"[{resident.town.nation.name} | {resident.town.name}] {resident.name} [{resident.pos}](https://earthmc.net/map/?worldname=earth&mapname=flat&zoom=8&x={resident.pos[0]}&y={resident.pos[1]}&z={resident.pos[2]})\n"
            embed = discord.Embed(title=f"{len(self.invading[enemy])} enemy/s near {enemy}", description=msg)
            await borders[enemy]["msg"].edit(embed=embed)
            if len(self.invading[enemy]) > 0:
                await self.bot.get_channel(731402228820213882).send(f"<@&{borders[enemy]['id']}>", tts=True, delete_after=0)
        return await self.loop()


def setup(bot):
    """
    Loads stuff so that it works
    """
    bot.add_cog(attack(bot))
