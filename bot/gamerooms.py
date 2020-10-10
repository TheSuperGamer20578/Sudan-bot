"""
Makes channels on demand only works in one server
"""
import random
import configparser

from discord.ext import commands

config = configparser.ConfigParser()
config.read("Config/config.ini")


class gamerooms(commands.Cog):
    """
    Main cog
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Make channels
        """
        if message.channel.category_id == 719401649050746911 and not message.author.bot:
            await message.guild.create_text_channel(random.choice(config["general"]["names"].split("\n")), category=message.guild.get_channel(719401649050746911))
            await message.channel.edit(category=message.guild.get_channel(719403010597453834))

    @commands.command()
    async def end(self, ctx):
        """Deletes a game room"""
        if ctx.channel.category_id == 719403010597453834:
            await ctx.channel.delete()


def setup(bot):
    """
    Initialize cog
    """
    bot.add_cog(gamerooms(bot))
