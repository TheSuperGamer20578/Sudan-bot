import discord
from discord.ext import commands
from subprocess import call
from core import trusted
import time


class update(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == 761747494693765151 and message.embeds:
            if " new commit" in message.embeds[0].title and message.embeds[0].title.startswith("[Sudan-bot:master] "):
                call(["git", "pull"])
                await self.bot.close()

    @commands.command()
    @commands.check(trusted)
    async def forceupdate(self, ctx):
        t = time.time()
        msg = await ctx.send("updating...")
        call(["git", "pull"])
        await msg.edit(f"updating... DONE!(took {time.time()-t}ms)")

    @commands.command()
    @commands.check(trusted)
    async def stopbot(self, ctx):
        await ctx.send("stopping...")
        await self.bot.close()


def setup(bot):
    gbot = bot
    bot.add_cog(update(bot))
