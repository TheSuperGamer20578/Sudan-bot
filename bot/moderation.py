import discord
import typing
import re
import time
from discord.ext import commands, tasks
from _util import Checks, set_db

def parse_punishment(argument):  
    punishments = {
        "none": 0,
        "warn": 1,
        "mute": 2,
        "kick": 3,
        "ban": 4
    }
    return punishments[argument.lower()]


def parse_time(argument):
    time = re.match(r"(\d*)(s|m|h|d|w|M|y)", argument)
    times = {
        "s": 1,
        "m": 60,
        "h": 60**2,
        "d": 60**2 * 24,
        "w": 60**2 * 24 * 7,
        "M": 60**2 * 24 * 30,
        "y": 60**2 * 24 * 365
    }
    if time is None:
        raise Exception
    return int(time.group(1)) * times[time.group(2)]


def human_delta(duration):
    delta = []
    if duration // (60**2 * 24 * 365) > 0:
        delta.append(f"{duration // (60**2 * 24 * 365)} years")
        duration %= 60**2 * 24 * 365
    if duration // (60**2 * 24 * 30) > 0:
        delta.append(f"{duration // (60**2 * 24 * 30)} months")
        duration %= 60**2 * 24 * 30
    if duration // (60**2 * 24) > 0:
        delta.append(f"{duration // (60**2 * 24)} days")
        duration %= 60**2 * 24
    if duration // 60**2 > 0:
        delta.append(f"{duration // 60**2} hours")
        duration %= 60**2
    if duration // 60 > 0:
        delta.append(f"{duration // 60} minutes")
        duration %= 60
    if duration > 0:
        delta.append(f"{duration} seconds")
    if len(delta) == 0:
        delta = ["Forever"]
    return ", ".join(delta)


class moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        set_db(bot.db)
        self.auto_unpunish.start()
    
    @commands.command(aliases=["pu"])
    @commands.check(Checks.mod)
    async def punish(self, ctx, users: commands.Greedy[discord.Member], punishment: typing.Optional[parse_punishment] = 0, duration: commands.Greedy[parse_time] = [], *, reason):
        if punishment == 3 and duration != 0:
            raise commands.BadArgument
        
        duration = sum(duration)
        
        await ctx.message.delete()

        ref = (f"https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/" +
               str(ctx.message.reference.message_id if ctx.message.reference is not None else ctx.channel.last_message_id))

        id = await self.bot.db.fetchval("SELECT incident_index FROM guilds WHERE id = $1", ctx.guild.id)
        await self.bot.db.execute("UPDATE guilds SET incident_index = incident_index + 1 WHERE id = $1", ctx.guild.id)
        
        await self.bot.db.execute("INSERT INTO incidents (guild, id, moderator, users, type_, time_, expires, comment, ref)" +
                                  "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)", ctx.guild.id, id, ctx.author.id, [user.id for user in users],
                                  punishment, time.time(), time.time() + duration, reason, ref)
        
        async def log(type):
            colours = {
                "Warn": 0xfc9003,
                "Mute": 0xc74c00,
                "Kick": 0xff0077,
                "Ban": 0xff0000
            }

            embed = discord.Embed(title=f"Incident #{id}", colour=colours[type])
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.add_field(name="Members involved", value=", ".join([member.mention for member in users]))
            embed.add_field(name="Punishemnt", value=type)
            if punishment in (1, 2, 4):
                embed.add_field(name="Duration", value=human_delta(duration))
            embed.add_field(name="Reason", value=f"{reason} ([ref]({ref}))", inline=False)

            for channel in [ctx.guild.get_channel(record["id"]) for record in await self.bot.db.fetch("SELECT id FROM channels WHERE log_type = 'moderation' AND guild_id = $1", ctx.guild.id)]:
                await channel.send(embed=embed)

        async def none():
            pass

        async def warn():
            await log("Warn")

        async def mute():
            role = ctx.guild.get_role(await self.bot.db.fetchval("SELECT mute_role FROM guilds WHERE id = $1", ctx.guild.id))
            for user in users:
                await user.add_roles(role, reason=f"Duration: {human_delta(duration)}. Incident #{id}: {reason}")
            await log("Mute")

        async def kick():
            for user in users:
                await user.kick(reason=f"Incident #{id}: {reason}")
            await log("Kick")

        async def ban():
            for user in users:
                await user.ban(reason=f"Duration: {human_delta(duration)}. Incident #{id}: {reason}", delete_message_days=0)
            await log("Ban")

        punishments = {
            0: none,
            1: warn,
            2: mute,
            3: kick,
            4: ban
        }

        await punishments[punishment]()
    
    @tasks.loop(seconds=1)
    async def auto_unpunish(self):
        incidents = await self.bot.db.fetch("SELECT incidents.users, incidents.type_, incidents.comment, incidents.id, incidents.guild, guilds.mute_role " +
                                            "FROM incidents " +
                                            "LEFT JOIN guilds ON incidents.guild = guilds.id " +
                                            "WHERE active = TRUE AND expires <= EXTRACT(EPOCH FROM NOW()) AND expires > time_")
        await self.bot.db.execute("UPDATE incidents SET active = FALSE WHERE active = TRUE AND expires <= EXTRACT(EPOCH FROM NOW()) AND expires > time_")

        for incident in incidents:
            guild = self.bot.get_guild(incident["guild"])

            async def none():
                pass

            async def mute():
                role = guild.get_role(await self.bot.db.fetchval("SELECT mute_role FROM guilds WHERE id = $1", guild.id))
                for user in [guild.get_member(member) for member in incident["users"]]:
                    await user.remove_roles(role, reason=f"Automatic unmute from incident #{incident['id']}: {incident['comment']}")

            async def ban():
                for user in [self.bot.fetch_user(user) for user in incident["users"]]:
                    await guild.unban(user, reason=f"Automatic unban from incident #{incident['id']}: {incident['comment']}")

            punishments = {
                0: none,
                1: none,
                2: mute,
                4: ban
            }
            await punishments[incident["type_"]]()


def setup(bot):
    bot.add_cog(moderation(bot))