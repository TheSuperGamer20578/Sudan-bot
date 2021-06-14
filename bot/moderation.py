import discord
import typing
import re
import time
from discord import commands
from _util import Checks, set_db

def parse_punishment_type(arg):    
    punishments = {
        "none": 0,
        "warn": 1,
        "mute": 2,
        "kick": 3,
        "ban": 4
    }
    return punishments[arg.lower()]

def parse_time(arg):
    time = re.match(r"(\d*)(s|m|h|d|w|M|y)\D*")
    times = {
        "s": 1,
        "m": 60,
        "h": 60**2,
        "d": 60**3,
        "w": 60**3 * 7,
        "M": 60**3 * 30,
        "y": 60**3 * 365
    }
    if time is None:
        raise Exception
    return time.group(1) * times[time.group(2)]

class moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        set_db(bot.db)
    
    @commands.command(aliases=["pu"])
    @commands.check(Checks.mod)
    async def punish(self, ctx, users: typing.greedy[discord.member], punishment: typing.Optional[parse_punishment_type] = 0, duration: typing.greedy[parse_time] = [], reason = None):
        if reason is None:
            raise discord.InvalidArgument
        
        await ctx.message.delete()

        id = await self.bot.db.fetchval("SELECT incident_index FROM guilds WHERE id = $1", ctx.guild.id)
        await self.bot.db.execute("UBDATE guilds SET incident_index = `incident_index` + 1 WHERE id = $1", ctx.guild.id)
        
        await self.bot.db.execute("INSERT INTO incidents (guild, id, moderator, users, type_, time_, expires, comment, ref)" +
                                  "($1,$2,$3,$4,%5,%6,$7,$8,$9)", ctx.guild.id, id, ctx.author.id, [user.id for user in users],
                                  punishment, time.time(), time.time() + sum(duration), reason,
                                  f"https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{ctx.message.reference.message_id}" or
                                  await ctx.channel.history(limit=1)[0].jump_url)
        

def setup(bot):
    bot.add_cog(moderation(bot))