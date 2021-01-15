"""
translator stuff
"""
import discord
from discord.ext import commands


class translate(commands.Cog):
    """
    translates stuff
    """
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    """
    start stuff
    """
    bot.add_cog(translate(bot))
