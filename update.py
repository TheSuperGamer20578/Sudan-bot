"""
Automatically updates the bot when there are changes to master
"""
from subprocess import call
import time
from asyncio import sleep
from discord.ext import commands
from core import trusted


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
                await sleep(15)
                call(["git", "pull"])
                await self.bot.close()

    @commands.command()
    @commands.check(trusted)
    async def forceupdate(self, ctx):
        """
        Forces the bot to download an update
        """
        start_time = time.time()
        msg = await ctx.send("updating...")
        call(["git", "pull"])
        await msg.edit(f"updating... DONE!(took {time.time()-start_time}ms)")

    @commands.command()
    @commands.check(trusted)
    async def stopbot(self, ctx):
        """
        Stops the bot
        """
        await ctx.send("stopping...")
        await self.bot.close()


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(update(bot))
