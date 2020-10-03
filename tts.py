import discord
from discord.ext import commands

voice_cat = 744136880261693470


class tts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def tts(self, ctx):
        if ctx.channel.category_id != voice_cat:
            return
        await ctx.send(f"-setup <#{ctx.channel.id}>", delete_after=1)
        await ctx.send("-join", delete_after=1)


def setup(bot):
    bot.add_cog(tts(bot))
