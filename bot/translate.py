"""
translator stuff
"""
import typing

import discord
from discord.ext import commands
from googletrans import Translator

translator = Translator()


def source_lang(arg):
    """
    detects if the arg is a source lang
    """
    if arg.startswith("?") and len(arg) == 3:
        return arg[1:]
    raise Exception


def dest_lang(arg):
    """
    detects if the arg is a dest lang
    """
    if arg.startswith("!") and len(arg) == 3:
        return arg[1:]
    raise Exception


class translate(commands.Cog):
    """
    translates stuff
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["tr"])
    async def translate(self, ctx, source: typing.Optional[source_lang] = "auto", dest: typing.Optional[dest_lang] = "en", *, text):
        """
        translates stuff
        """
        translation = translator.translate(text, dest, source)
        embed = discord.Embed(title=f"{translation.src} -> {translation.dest}",
                              description=translation.text)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)


def setup(bot):
    """
    start stuff
    """
    bot.add_cog(translate(bot))
