"""
Automatically updates the bot when there are changes to master
"""
import time
from subprocess import call

from discord.ext import commands

from _Util import Checks


class Update(commands.Cog):
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
                await self.bot.log.info("Updating...")
                await self.bot.log.public("Update detected, pulling...")
                start_time = time.time()
                call(["git", "pull"])
                await self.bot.log.debug(f"Update took {time.time() - start_time}ms")
                await self.bot.log.error("Restarting after update...")
                await self.bot.log.public("Restarting...")
                await self.bot.close()

    @commands.command()
    @commands.check(Checks.trusted)
    async def forceupdate(self, ctx):
        """
        Forces the bot to download an update
        """
        msg = await ctx.send("Updating...")
        await self.bot.log.info(f"Update started by {ctx.author.name}")
        start_time = time.time()
        call(["git", "pull"])
        await self.bot.log.debug(f"Update took {time.time() - start_time}ms")
        await msg.edit(f"Updating... DONE!(took {time.time()-start_time}ms)")

    @commands.command()
    @commands.check(Checks.trusted)
    async def restartbot(self, ctx):
        """Restarts the bot"""
        await ctx.send("Restarting...")
        await self.bot.log.error(f"Restart initiated by {ctx.author.name}")
        await self.bot.log.public("Restarting...")
        await self.bot.close()


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(Update(bot))
