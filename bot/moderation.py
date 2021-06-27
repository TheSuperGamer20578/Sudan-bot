import discord
import typing
import re
import time
import datetime
from discord.ext import commands, tasks
from discord_components import DiscordComponents, Button, ButtonStyle
from asyncio.exceptions import TimeoutError
from _util import Checks, set_db, RED, GREEN


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
    time_ = re.match(r"(\d*)([smhdwMy])", argument)
    times = {
        "s": 1,
        "m": 60,
        "h": 60**2,
        "d": 60**2 * 24,
        "w": 60**2 * 24 * 7,
        "M": 60**2 * 24 * 30,
        "y": 60**2 * 24 * 365
    }
    if time_ is None:
        raise Exception
    return int(time_.group(1)) * times[time_.group(2)]


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


def human_delta_short(duration):
    delta = []
    if duration // (60**2 * 24 * 365) > 0:
        delta.append(f"{duration // (60**2 * 24 * 365)}y")
        duration %= 60**2 * 24 * 365
    if duration // (60**2 * 24 * 30) > 0:
        delta.append(f"{duration // (60**2 * 24 * 30)}M")
        duration %= 60**2 * 24 * 30
    if duration // (60**2 * 24) > 0:
        delta.append(f"{duration // (60**2 * 24)}d")
        duration %= 60**2 * 24
    if duration // 60**2 > 0:
        delta.append(f"{duration // 60**2}h")
        duration %= 60**2
    if duration // 60 > 0:
        delta.append(f"{duration // 60}m")
        duration %= 60
    if duration > 0:
        delta.append(f"{duration}s")
    if len(delta) == 0:
        delta = ["Forever"]
    return "".join(delta)


class moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        set_db(bot.db)
        DiscordComponents(bot)
        self.auto_unpunish.start()
    
    @commands.command(aliases=["pu"])
    @commands.check(Checks.mod)
    async def punish(self, ctx, users: commands.Greedy[discord.Member], punishment: typing.Optional[parse_punishment] = 0, duration: commands.Greedy[parse_time] = None, *, reason):
        if duration is None:
            duration = []
        if punishment == 3 and duration != []:
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
        
        async def log(type_):
            colours = {
                "Warn": 0xfc9003,
                "Mute": 0xc74c00,
                "Kick": 0xff0077,
                "Ban": 0xff0000
            }

            embed = discord.Embed(title=f"Incident #{id}", colour=colours[type_])
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.add_field(name="Members involved", value=", ".join([member.mention for member in users]))
            embed.add_field(name="Punishemnt", value=type_)
            if punishment != 3:
                embed.add_field(name="Duration", value=human_delta(duration))
            embed.add_field(name="Reason", value=f"{reason} ([ref]({ref}))", inline=False)

            for channel in [ctx.guild.get_channel(record["id"]) for record in await self.bot.db.fetch("SELECT id FROM channels WHERE log_type = 'moderation' AND guild_id = $1", ctx.guild.id)]:
                await channel.send(embed=embed)

        async def dm(title, message, colour):
            embed = discord.Embed(title=title, description=message, colour=colour)
            for user in users:
                await user.send(embed=embed)

        async def none():
            pass

        async def warn():
            await dm("Warning!", f"You have been warned in {ctx.guild.name} for {reason} for {human_delta(duration)}! Incident #{id} ([ref]({ref}))", 0xfc9003)
            await log("Warn")

        async def mute():
            await dm("Muted!", f"You have been muted in {ctx.guild.name} for {reason} for {human_delta(duration)}! Incident #{id} ([ref]({ref}))", 0xc74c00)
            role = ctx.guild.get_role(await self.bot.db.fetchval("SELECT mute_role FROM guilds WHERE id = $1", ctx.guild.id))
            for user in users:
                await user.add_roles(role, reason=f"Duration: {human_delta(duration)}. Incident #{id}: {reason}")
            await log("Mute")

        async def kick():
            await dm("Kicked!", f"You have been kicked from {ctx.guild.name} for {reason}! Incident #{id} ([ref]({ref}))", 0xff0077)
            for user in users:
                await user.kick(reason=f"Incident #{id}: {reason}")
            await log("Kick")

        async def ban():
            await dm("Banned!", f"You have been banned from {ctx.guild.name} for {reason} for {human_delta(duration)}! Incident #{id} ([ref]({ref}))", 0xff0000)
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

    @commands.command(aliases=["i", "in", "inc"])
    @commands.check(Checks.mod)
    async def incident(self, ctx, id: int):
        incident_ = await self.bot.db.fetchrow("SELECT users, time_, type_, comment, ref, moderator, expires, active, expires - time_ AS duration FROM incidents WHERE guild = $1 AND id = $2", ctx.guild.id, id)
        await ctx.message.delete()
        if incident_ is None:
            embed = discord.Embed(title=f"Incident #{id} does not exist!", colour=RED)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)
            return

        punishments = {
            0: "None",
            1: "Warn",
            2: "Mute",
            3: "Kick",
            4: "Ban"
        }
        colours = {
            0: 0x787878,
            1: 0xfc9003,
            2: 0xc74c00,
            3: 0xff0077,
            4: 0xff0000
        }

        embed = discord.Embed(title=f"Incident #{id}{' (ACTIVE)' if incident_['active'] and incident_['type_'] != 3 else ''}", colour=colours[incident_["type_"]], timestamp=datetime.datetime.utcfromtimestamp(incident_["time_"]))
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.add_field(name="Moderator", value=f"<@{incident_['moderator']}>")
        embed.add_field(name="Members involved",
                        value=", ".join([f"<@{member}>" for member in incident_["users"]]))
        embed.add_field(name="Punishemnt", value=punishments[incident_["type_"]])
        if incident_["type_"] != 3:
            embed.add_field(name="Duration", value=human_delta(incident_["duration"]))
        embed.add_field(name="Reason", value=f"{incident_['comment']} ([ref]({incident_['ref']}))",
                        inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def warns(self, ctx):
        records = await self.bot.db.fetch("SELECT id, comment, ref, expires, time_ FROM incidents WHERE active = TRUE AND type_ = 1 AND guild = $1 AND $2 = ANY(users) ORDER BY id", ctx.guild.id, ctx.author.id)
        await ctx.message.delete()
        if len(records) == 0:
            embed = discord.Embed(title="You have no active warnings!", colour=GREEN)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(title=f"You have {len(records)} active warnings!", description="\n".join([f"[{human_delta_short(int(time.time()) - record['time_'])} ago #{record['id']}{(f' expires in ' + human_delta_short(record['expires'] - int(time.time()))) if record['expires'] > record['time_'] else ''}: {record['comment']}]({record['ref']})" for record in records]), colour=RED)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["h", "hist"])
    @commands.check(Checks.mod)
    async def history(self, ctx, person: discord.User):
        records = await self.bot.db.fetch("SELECT id, comment, ref, expires, time_, type_, active FROM incidents WHERE guild = $1 AND $2 = ANY(users) ORDER BY id", ctx.guild.id, person.id)
        await ctx.message.delete()
        types = {
            0: "Note",
            1: "Warn",
            2: "Mute",
            3: "Kick",
            4: "Ban"
        }
        pages_active: list
        pages_inactive: list
        length: int
        pages: int

        index = 0
        active = True
        notes = False

        def compute_lists():
            nonlocal length, pages, pages_active, pages_inactive
            list_active = [f"[{human_delta_short(int(time.time()) - record['time_'])} ago #{record['id']} {types[record['type_']]}{(f' expires in ' + human_delta_short(record['expires'] - int(time.time()))) if record['expires'] > record['time_'] else ''}: {record['comment']}]({record['ref']})" for record in records if record["active"] and (record["type_"] > 0 or notes)]
            list_inactive = [f"[{human_delta_short(int(time.time()) - record['time_'])} ago #{record['id']} {types[record['type_']]}: {record['comment']}]({record['ref']})" for record in records if not record['active'] and (record["type_"] > 0 or notes)]
            pages_active = ["\n".join(list_active[n : n+10]) for n in range(0, len(list_active), 10)]
            pages_inactive = ["\n".join(list_inactive[n: n + 10]) for n in range(0, len(list_inactive), 10)]
            if len(pages_active) == 0:
                pages_active = [""]
            if len(pages_inactive) == 0:
                pages_inactive = [""]
            length = len(list_active if active else list_inactive)
            pages = len(pages_active if active else pages_inactive)

        compute_lists()

        def paged_embed():
            page = (pages_active if active else pages_inactive)[index]
            embed = discord.Embed(title=f"{person.display_name} has {length} {'active' if active else 'inactive'} punishments{' and notes' if notes else ''}!", description=page, colour=GREEN if length == 0 else RED)
            embed.set_footer(text=f"Page {index+1}/{pages}")
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            return embed

        def components():
            return [
                [Button(label="<<", disabled=index == 0, style=ButtonStyle.blue, id="first"),
                 Button(label="<", disabled=index == 0, style=ButtonStyle.blue, id="previous"),
                 Button(label=">", disabled=index == pages - 1, style=ButtonStyle.blue, id="next"),
                 Button(label=">>", disabled=index == pages - 1, style=ButtonStyle.blue, id="last")],
                [Button(label="Active", disabled=active, style=ButtonStyle.green, id="active"),
                 Button(label="Inactive", disabled=not active, style=ButtonStyle.red, id="inactive")],
                [Button(label="Show notes", style=ButtonStyle.grey, disabled=notes, id="notes")]
            ]
        message = await ctx.send(embed=paged_embed(), components=components())

        try:
            while True:
                interaction = await self.bot.wait_for("button_click", timeout=5*60, check=lambda i: i.message == message)
                if interaction.user != ctx.author:
                    await interaction.respond(content="Only the person who triggered the command can push buttons!")
                    continue
                elif interaction.custom_id == "first":
                    index = 0
                elif interaction.custom_id == "previous":
                    index -= 1
                elif interaction.custom_id == "next":
                    index += 1
                elif interaction.custom_id == "last":
                    index = pages - 1
                elif interaction.custom_id == "active":
                    active = True
                    index = 0
                    compute_lists()
                elif interaction.custom_id == "inactive":
                    active = False
                    index = 0
                    compute_lists()
                elif interaction.custom_id == "notes":
                    notes = True
                    index = 0
                    compute_lists()
                await message.edit(embed=paged_embed(), components=components())
                await interaction.respond(type=6)

        except TimeoutError:
            await message.edit(embed=paged_embed(), components=[])

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
