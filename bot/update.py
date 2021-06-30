"""
Automatically updates the bot when there are changes to master
"""
import time
import os
from subprocess import call

import discord
from discord.ext import commands

from _util import Checks


class update(commands.Cog):
    """
    Main class
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Checks for updates
        """
        if message.channel.id == 761747494693765151 and message.embeds:
            if " new commit" in message.embeds[0].title and message.embeds[0].title.startswith("[Sudan-bot:master] "):
                embed = discord.Embed(title="Update detected pulling...")
                await self.bot.get_channel(int(os.getenv("LOG_CHANNEL"))).send(embed=embed)
                call(["git", "pull"])
                embed = discord.Embed(title="Restarting/stopping...")
                await self.bot.get_channel(int(os.getenv("LOG_CHANNEL"))).send(embed=embed)
                await self.bot.close()

    @commands.command()
    @commands.check(Checks.trusted)
    async def forceupdate(self, ctx):
        """
        Forces the bot to download an update
        """
        start_time = time.time()
        msg = await ctx.send("updating...")
        embed = discord.Embed(title="Pulling update...")
        await self.bot.get_channel(int(os.getenv("LOG_CHANNEL"))).send(embed=embed)
        call(["git", "pull"])
        await msg.edit(f"updating... DONE!(took {time.time()-start_time}ms)")

    @commands.command()
    @commands.check(Checks.trusted)
    async def stopbot(self, ctx):
        """
        Stops the bot
        """
        await ctx.send("stopping...")
        embed = discord.Embed(title="Restarting/stopping...")
        await self.bot.get_channel(int(os.getenv("LOG_CHANNEL"))).send(embed=embed)
        await self.bot.close()


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(update(bot))
