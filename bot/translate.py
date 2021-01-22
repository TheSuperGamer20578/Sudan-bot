"""
translator stuff
"""
import typing
import os
from requests import post

import discord
from discord.ext import commands


def source_lang(arg):
    """
    detects if the arg is a source lang
    """
    if arg.startswith("!") and len(arg) == 3:
        return arg[1:]
    raise Exception


def dest_lang(arg):
    """
    detects if the arg is a dest lang
    """
    if arg.startswith("?") and len(arg) == 3:
        return arg[1:]
    raise Exception


class translate(commands.Cog):
    """
    translates stuff
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["tr"])
    async def translate(self, ctx, dest: typing.Optional[dest_lang] = "en", source: typing.Optional[source_lang] = None, *, text):
        """
        translates stuff
        """
        src = f"&from={source}" if source is not None else ""
        resp = post(f"https://api.cognitive.microsofttranslator.com/translate?api-version=3.0{src}&to={dest}",
                    headers={
                        "Ocp-Apim-Subscription-Key": os.getenv("MICROSOFT_TRANSLATE_KEY"),
                        "Ocp-Apim-Subscription-Region": os.getenv("MICROSOFT_TRANSLATE_REGION"),
                        "Content-Type": "application/json"
                    },
                    json=[{"Text": text}])
        resp.raise_for_status()
        translation = resp.json()[0]
        if "detectedLanguage" in translation:
            lang = translation["detectedLanguage"]["language"]
        else:
            lang = source
        embed = discord.Embed(title=f"{lang.upper()} -> {translation['translations'][0]['to'].upper()}",
                              description=translation["translations"][0]["text"])
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)


def setup(bot):
    """
    start stuff
    """
    bot.add_cog(translate(bot))
