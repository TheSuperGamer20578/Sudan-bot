"""
Makes channels on demand only works in one server
"""
import random
from discord.ext import commands


class gamerooms(commands.Cog):
    """
    Main cog
    """
    def __init__(self, bot):
        self.bot = bot
        with open("Config/names.txt", "r") as f:
            self.names = f.read().split("\n")

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Make channels
        """
        if message.channel.category_id == 719401649050746911 and not message.author.bot:
            await message.guild.create_text_channel(random.choice(self.names), category=message.guild.get_channel(719401649050746911))
            await message.channel.edit(category=message.guild.get_channel(719403010597453834))

    @commands.command()
    async def end(self, ctx):
        """Deletes a game room"""
        if ctx.channel.category_id == 719403010597453834:
            # TODO add logging
            await ctx.channel.delete()


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(gamerooms(bot))
