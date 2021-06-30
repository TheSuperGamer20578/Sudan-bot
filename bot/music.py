"""
Basic music functionality
"""
from ctypes import util
import os
import threading
import shutil
import functools

import discord
import youtube_dl
from discord.ext import commands
from discord.utils import get

from _util import Checks, GREEN, RED
queue = {}
np = {}
if os.name != "nt":
    discord.opus.load_opus(util.find_library('opus'))
    if not discord.opus.is_loaded():
        raise RuntimeError('Opus failed to load')


def check_dj(ctx):
    """
    Check to see if user is a mod or in VC alone
    """
    return len([vcuser for vcuser in ctx.author.voice.channel.members if not vcuser.bot]) <= 1 or Checks.mod(ctx)


def add(key, *url):
    """
    Adds a song to the queue
    """
    url = " ".join(url)
    ytdl_options = {
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }]
    }
    if not url.startswith("https://"):
        ytdl_options["default_search"] = "auto"
    with youtube_dl.YoutubeDL(ytdl_options) as ytdl:
        ytdl.download([url])
    name = None
    for file in os.listdir():
        if file.endswith(".mp3"):
            name = '-'.join(file.split('-')[:-1])
            try:
                os.rename(file, f"music/{key}/{name}.mp3")
            except FileExistsError:
                pass
    for file in os.listdir():
        if file.endswith(".webm") or file.endswith(".mp3"):
            os.remove(file)
    queue[str(key)].append(name)


def run(self, guild, key):
    """
    Plays music from the queue
    """
    if len(queue[str(key)]) > 0:
        voice = get(self.bot.voice_clients, guild=guild)
        voice.play(discord.FFmpegPCMAudio(f"music/{guild.id}/{queue[str(key)][0]}.mp3"), after=lambda e: run(self, guild, key))
        np[str(key)] = queue[str(key)][0]
        del queue[str(key)][0]
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = 0.3
    else:
        np[str(key)] = None


class music(commands.Cog):
    """
    Discord.py cog
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["j"])
    async def join(self, ctx):
        """
        Makes the bot join your VC
        """
        channel = ctx.author.voice.channel
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            if Checks.mod(ctx):
                await voice.move_to(channel)
            else:
                raise commands.CheckFailure()
        else:
            await channel.connect()
        queue[str(ctx.guild.id)] = []
        np[str(ctx.guild.id)] = None
        os.makedirs(f"music/{ctx.guild.id}")
        embed = discord.Embed(title=f"Connected to {channel.name}!", colour=GREEN)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command(aliases=["l"])
    @commands.check(check_dj)
    async def leave(self, ctx):
        """
        Makes the bot leave your VC
        """
        channel = ctx.author.voice.channel
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            del queue[str(ctx.guild.id)]
            del np[str(ctx.guild.id)]
            voice.stop()
            await voice.disconnect()
            shutil.rmtree(f"music/{ctx.guild.id}")
            embed = discord.Embed(title=f"Disconnected from {channel.name}", colour=GREEN)
        else:
            embed = discord.Embed(title="Im not in a VC!", colour=RED)
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command(aliases=["p"])
    async def play(self, ctx, *, url):
        """
        Adds a song to the queue this may take a while especially for longer songs **DO NOT TELL THE BOT TO QUEUE 2 SONGS AT THE SAME TIME**
        """
        thread = threading.Thread(target=add, args=(ctx.guild.id, url))
        thread.start()
        await self.bot.loop.run_in_executor(None, functools.partial(thread.join))
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if not voice.is_playing():
            thread = threading.Thread(target=run, args=(self, ctx.guild, ctx.guild.id))
            thread.start()
        embed = discord.Embed(title=f"Queued \"{queue[str(ctx.guild.id)][-1]}\"")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command(aliases=["s", "n", "next"])
    @commands.check(check_dj)
    async def skip(self, ctx):
        """
        Skips the current song
        """
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        voice.stop()
        embed = discord.Embed(title="Stopped music")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command(aliases=["vol", "v"])
    @commands.check(check_dj)
    async def volume(self, ctx, vol: float):
        """
        Changes the volume, there is a limit of 50% volume
        """
        if vol > 50.0:
            embed = discord.Embed(title="It is unsafe to go that high!", colour=RED)
        else:
            voice = get(self.bot.voice_clients, guild=ctx.guild)
            voice.source = discord.PCMVolumeTransformer(voice.source)
            voice.source.volume = vol / 10
            embed = discord.Embed(title="Volume changed", description=f"New volume: {vol}%")
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command(aliases=["q", "que"])
    async def queue(self, ctx):
        """
        Displays the queue
        """
        embed = discord.Embed(title="Queue", description=f"Now playing: {np[str(ctx.guild.id)]}\n\n"+"\n".join(queue[str(ctx.guild.id)]))
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.check(Checks.trusted)
    async def rick(self, ctx, guild: int):
        """
        Rick-rolls the server with the specified ID
        """
        voice = get(self.bot.voice_clients, guild=self.bot.get_guild(guild))
        queue_temp = [np[str(guild)]]+queue[str(guild)]
        queue[str(guild)] = None
        voice.stop()
        voice.play(discord.FFmpegPCMAudio("music/rick.mp3"), after=lambda e: run(self, self.bot.get_guild(guild), guild))
        queue[str(guild)] = queue_temp
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = 0.6
        await ctx.send(f"Rick-rolling {self.bot.get_guild(guild).name}")

    @commands.command(aliases=["np"])
    async def nowplaying(self, ctx):
        """
        Shows what song is currently playing
        """
        embed = discord.Embed(title="Now playing:", description=np[str(ctx.guild.id)])
        embed.set_author(name=ctx.author.nick if ctx.author.nick else ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)


def setup(bot):
    """
    Initiates cog
    """
    bot.add_cog(music(bot))
