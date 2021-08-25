"""
Contains fun stuff
"""
import re
import asyncio
from os import getenv
from random import shuffle, choice

import discord
from discord.ext import commands
from discord_components import Select, SelectOption, Button, ButtonStyle

from _Util import Checks, GREEN, RED, BLUE
from Moderation import parse_time, human_delta

GOLD = getenv("GOLD_EMOJI")
BAMBOO = getenv("BAMBOO_EMOJI")


async def check_no_chain_forever(ctx):
    """Check that chainforever is not active"""
    async with ctx.bot.pool.acquire() as db:
        return await db.fetchval("SELECT chain_forever FROM channels WHERE id = $1", ctx.channel.id) is None


async def check_trivia_role(ctx, bot=None):
    """Checks if someone is allowed to do trivia stuff"""
    async with (bot or ctx.bot).pool.acquire() as db:
        for role in await db.fetchval("SELECT trivia_roles FROM guilds WHERE id = $1", ctx.guild.id):
            if role in [r.id for r in ctx.author.roles]:
                return True
        return False


async def transfer_gold(bot, user_a, user_b, amount):
    """Transfers gold from one user to another"""
    async with bot.pool.acquire() as db:
        await db.execute("UPDATE users SET gold = gold - $2 WHERE id = $1", user_a.id, amount)
        await db.execute("UPDATE users SET gold = gold + $2 WHERE id = $1", user_b.id, amount)


class NotEnoughCurrencyException(commands.CheckFailure):
    """Error for when someone doesnt have enough currency"""
    def __init__(self, currency, required):
        self.currency = currency
        self.required = required
        super().__init__()


def require_gold(amount):
    """Check that the user invoking the command has enough gold"""
    async def predicate(ctx):
        async with ctx.bot.pool.acquire() as db:
            if await db.fetchval("SELECT gold FROM users WHERE id = $1", ctx.author.id) < amount:
                raise NotEnoughCurrencyException(GOLD, amount)
            return True
    return commands.check(predicate)


class Fun(commands.Cog):
    """
    The main class for this file
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def lmgtfy(self, ctx, *, query):
        """
        When someone bothers you with their questions use this command to link them to google after they have a little laugh
        """
        await ctx.message.delete()
        embed = discord.Embed(title=query,
                              url=f"https://lmgtfy.com/?q={query.replace(' ', '%20')}&pp=1&iie=1")
        embed.set_author(name=ctx.author.nick, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.check(
        lambda ctx: "sudont" not in [role.name for role in ctx.author.roles])
    async def sudo(self, ctx, user: discord.Member, *, message):
        """
        Mimics another user
        """
        await ctx.message.delete()
        webhook = await ctx.channel.create_webhook(
            name=user.nick if user.nick is not None else user.name)
        await webhook.send(message,
                           avatar_url=user.avatar_url)
        await webhook.delete()

    @commands.check(check_no_chain_forever)
    @commands.command()
    async def chain(self, ctx, *, thing):
        """
        Starts a chain
        """
        if thing.startswith("$counting:"):
            if thing.split(":", 1)[1] == "" or any(char not in "0123456789" for char in thing.split(":", 1)[1]) or thing.split(":", 1)[1][0] == "0":
                raise commands.BadArgument
            await ctx.send(f"Counting started at: {thing.split(':', 1)[1]}")
        else:
            await ctx.send(f"New chain: {thing}")
        await self.bot.db.execute("UPDATE channels SET last_chain = NULL, chain = $2 WHERE id = $1", ctx.channel.id, thing)

    @commands.check(Checks.admin)
    @commands.command()
    async def chainforever(self, ctx, *, thing=None):
        """Starts a chain that restarts when broken"""
        await ctx.message.delete()
        if thing is None:
            embed = discord.Embed(title="Chain disabled", colour=RED)
        else:
            if thing.startswith("$counting:"):
                if thing.split(":", 1)[1] == "" or any(char not in "0123456789" for char in thing.split(":", 1)[1]) or thing.split(":", 1)[1][0] == "0":
                    raise commands.BadArgument
            embed = discord.Embed(title="Chain updated", description=f"New chain: {thing}", colour=GREEN)
        await self.bot.db.execute("UPDATE channels SET last_chain = NULL, chain_forever = $2, chain = $2 WHERE id = $1", ctx.channel.id, thing)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    async def chain_check(self, msg):
        """
        Checks to see if chain is broken
        """
        if isinstance(msg.channel, discord.DMChannel):
            return
        bot = self.bot
        async with self.bot.pool.acquire() as db:
            chain_ = await db.fetchrow("SELECT chain, chain_length, chain_forever FROM channels WHERE id = $1", msg.channel.id)
            chain = chain_["chain"]
            length = chain_["chain_length"]
            forever = chain_["chain_forever"]

            async def cbreak():
                """
                If the chain is broken say so and update DB
                """
                if forever is not None:
                    if any(msg.content.startswith(f"{prefix}chainforever") for prefix in getenv("PREFIXES").split(",")) and await Checks.admin(msg, bot):
                        return
                    embed = discord.Embed(title="Chain broken!", description=f"{msg.author.mention} broke the chain!", colour=RED)
                    embed.add_field(name="Length", value=length)
                    embed.set_author(name=msg.author.display_name, icon_url=msg.author.avatar_url)
                    message = await msg.reply(embed=embed)
                    if length >= int(getenv("CHAIN_PIN_THRESHOLD")):
                        await message.pin()
                else:
                    await msg.channel.send(f"{msg.author.mention} broke the chain! start a new chain with `.chain <thing>`. Chain length: {length}")
                await msg.add_reaction("❌")
                break_role = await db.fetchval("SELECT chain_break_role FROM guilds WHERE id = $1", msg.guild.id)
                if break_role is not None:
                    await msg.author.add_roles(msg.guild.get_role(break_role))
                await db.execute("UPDATE channels SET chain = $2, chain_length = 0, last_chain = NULL WHERE id = $1", msg.channel.id, forever)

            if chain is None or msg.author.bot:
                return
            if chain.startswith("$counting:"):
                num = int(chain.split(":")[1])
                if msg.content != str(num):
                    return await cbreak()
                num += 1
                chain = f"$counting:{num}"
                await db.execute("UPDATE channels SET chain = $2 WHERE id = $1", msg.channel.id, chain)
            elif msg.content != chain:
                return await cbreak()
            if msg.author.id == await db.fetchval("SELECT last_chain FROM channels WHERE id = $1", msg.channel.id):
                return await cbreak()
            await db.execute("UPDATE channels SET last_chain = $2, chain_length = chain_length + 1 WHERE id = $1", msg.channel.id, msg.author.id)
            if (msg.content == "100" and chain.startswith("$")) or length == 100:
                await msg.add_reaction("💯")
            else:
                await msg.add_reaction("✅")

    async def dad_mode(self, message):
        """
        dad mode
        """
        async with self.bot.pool.acquire() as db:
            if not await db.fetchval("SELECT dad_mode FROM users WHERE id = $1", message.author.id):
                return
        phrases = {
            "i am {}": "Hi {}! I am Dad",
            "i'm {}": "Hi {}! I'm Dad",
            "im {}": "Hi {}! Im Dad",
            "わたしは{}です": "こんにちわ{}さん！わたしはおとうさんです",
            "私は{}です": "こんにちわ{}さん！私はお父さんです"
        }
        for said, reply in zip(phrases.keys(), phrases.values()):
            match = re.search(said.format(r"(.*)"), message.content.lower())
            if match:
                await message.channel.send(reply.format(match.group(1)))

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        runs stuff that has to run on_message
        """
        await self.dad_mode(message)
        await self.chain_check(message)

    @commands.command()
    @commands.check(check_trivia_role)
    async def trivia(self, ctx, title, question, answer, *answers):
        """Starts a trivia"""
        await ctx.message.delete()
        embed = discord.Embed(title=title, description=question, colour=0xff564a)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        options = [SelectOption(label=option, value=f"-{option}") for option in answers]
        options.append(SelectOption(label=answer, value=f"+{answer}"))
        shuffle(options)
        await ctx.send(embed=embed, components=[Select(placeholder="Select an answer", options=options, custom_id="trivia"), Button(label="Info", style=ButtonStyle.grey, id="trivia.info", emoji="ℹ")])

    @commands.command()
    @commands.check(check_trivia_role)
    async def triviaanswers(self, ctx, message: int):
        """Shows how everyone answered a question"""
        await ctx.message.delete()
        async with self.bot.pool.acquire() as db:
            answers = await db.fetch("SELECT member, answer, correct FROM trivia WHERE id = $1", message)
        if len(answers) == 0:
            embed = discord.Embed(title="The selected message does not have any answers or is not a trivia message", colour=RED)
        else:
            embed = discord.Embed(title="Trivia answers", colour=0x4287f5)
            options = {(answer["answer"], answer["correct"]) for answer in answers}
            for option in options:
                tick = ":white_check_mark: " if option[1] else ""
                embed.add_field(name=tick + option[0], value="\n".join(f"<@{answer['member']}>" for answer in answers if answer["answer"] == option[0]))
            embed.set_footer(text=f"ID: {message}")
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["bal"])
    async def balance(self, ctx, user: discord.Member = None):
        """Shows a user's balance"""
        if user is None:
            user = ctx.author
        async with self.bot.pool.acquire() as db:
            data = await db.fetchrow("SELECT gold, bamboo FROM users WHERE id = $1", user.id)
        embed = discord.Embed(title=f"{user.display_name}'s balance", description=f"Gold: {data['gold']}{GOLD}\nBamboo: {data['bamboo']}{BAMBOO}", colour=BLUE)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.group()
    @commands.check(Checks.trusted)
    async def eco(self, ctx):
        """Manages the economy"""

    @eco.group()
    async def gold(self, ctx):
        """Manages gold stuff"""

    @gold.command()
    async def transfer(self, ctx, user_a: discord.User, user_b: discord.User, amount: int):
        """Transfers gold from one user to another"""
        await transfer_gold(self.bot, user_a, user_b, amount)
        await ctx.send(f"Transferred {amount}{GOLD} from {user_a.name} to {user_b.name}")

    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx, no_mentions: bool = False):
        """Shows a leaderboard"""
        await ctx.message.delete()
        async with self.bot.pool.acquire() as db:
            gold = await db.fetch("SELECT id, gold FROM users ORDER BY gold DESC LIMIT 10")
            bamboo = await db.fetch("SELECT id, bamboo FROM users ORDER BY bamboo DESC LIMIT 10")
        embed = discord.Embed(title="Leaderboard", colour=BLUE)
        for iteration, record in enumerate(gold):
            record = dict(record)
            user = self.bot.get_user(record["id"])
            record["user"] = f"{user.name}#{user.discriminator}: " if no_mentions else user.mention
            gold[iteration] = record
        for iteration, record in enumerate(bamboo):
            record = dict(record)
            user = self.bot.get_user(record["id"])
            record["user"] = f"{user.name}#{user.discriminator}: " if no_mentions else user.mention
            bamboo[iteration] = record
        embed.add_field(name="Gold", value="\n".join(f"{record['user']}{record['gold']}{GOLD}" for record in gold), inline=False)
        embed.add_field(name="Bamboo", value="\n".join(f"{record['user']}{record['bamboo']}{BAMBOO}" for record in bamboo), inline=False)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    @require_gold(-10)
    async def tictactoe(self, ctx, user: discord.Member, bet: int = 0, time: parse_time = 60, large: bool = False):
        """Tic tac toe"""
        assert 5 <= time <= 600
        await ctx.message.delete()
        message = await ctx.send(f"{user.mention} You have been invited to play {'large ' if large else ''}tic tac toe with a {human_delta(time)} time limit for {bet}{GOLD} by {ctx.author.mention}",
                                 components=[Button(label="Join", style=ButtonStyle.green)])
        try:
            while True:
                interaction = await self.bot.wait_for("button_click", timeout=30, check=lambda i: i.message == message)
                if interaction.user != user:
                    await interaction.respond(content="Only the person who was invited can accept!")
                    continue
                await transfer_gold(self.bot, ctx.author, self.bot.user, bet)
                await transfer_gold(self.bot, user, self.bot.user, bet)
                await interaction.respond(type=6)
                break
        except asyncio.exceptions.TimeoutError:
            await message.edit(f"~~{user.mention} You have been invited to play tic tac toe for {bet}{GOLD} by {ctx.author.mention}~~\n**Invite expired**", components=[])
            return

        grid = [[None] * (5 if large else 3) for _ in range(5 if large else 3)]
        turn = choice((True, False))
        styles = {
            True: ButtonStyle.blue,
            False: ButtonStyle.red,
            None: ButtonStyle.grey
        }
        users = {
            True: ctx.author,
            False: user
        }

        def msg(active, message=None):
            if message is None:
                message = f"It's {users[turn].mention}'s turn"
            embed = discord.Embed(title="Tic tac toe", description=f"{message}\n:blue_square:{ctx.author.mention}\n:red_square:{user.mention}\n\n{bet}{GOLD}", colour=BLUE)
            components = [
                [Button(label="\N{zero width space}", style=styles[button], disabled=not (active and button is None) or (large and row_number == 2 == column),
                        custom_id=f"{row_number},{column}") for column, button in enumerate(row)] for row_number, row in enumerate(grid)]
            return {
                "embed": embed,
                "components": components
            }

        def check_space():
            for row in grid:
                yield None in row

        def check_win(board):
            if [True, True, True] in board:
                return True
            if [False, False, False] in board:
                return False
            if board[0][0] is not None and len(set(board[row][row] == board[0][0] for row in range(3))) == 1:
                return board[0][0]
            if board[0][0] is not None and len(set(board[-(row + 1)][row] == board[-1][0] for row in range(3))) == 1:
                return board[-1][0]
            for column in range(3):
                if board[0][column] is not None and len(set(board[row][column] == board[0][column] for row in range(3))) == 1:
                    return board[0][column]
            return None

        await message.edit("", **msg(True))
        try:
            while True:
                interaction = await self.bot.wait_for("button_click", timeout=time, check=lambda i: i.message == message)
                if interaction.user != users[turn]:
                    await interaction.respond(content="It's not your turn!")
                    continue
                await interaction.respond(type=6)
                button = interaction.custom_id.split(",")
                grid[int(button[0])][int(button[1])] = turn
                turn = not turn
                if True not in check_space():
                    await message.edit(**msg(False, "**It's a draw!**"))
                    await transfer_gold(self.bot, self.bot.user, ctx.author, bet)
                    await transfer_gold(self.bot, self.bot.user, user, bet)
                    return
                for offset_y in range(len(grid) - 2):
                    for offset_x in range(len(grid[0]) - 2):
                        winner = check_win([board[offset_x : offset_x+3] for board in grid[offset_y : offset_y+3]])
                        if winner is not None:
                            winner = users[winner]
                            await message.edit(**msg(False, f"**{winner.mention} won!**"))
                            await transfer_gold(self.bot, self.bot.user, winner, bet * 2)
                            return
                await message.edit(**msg(True))
        except asyncio.exceptions.TimeoutError:
            await message.edit(**msg(False, f"**{users[turn].mention} ran out of time!**"))
            await transfer_gold(self.bot, self.bot.user, users[turn], bet * 2)

    @commands.Cog.listener()
    async def on_select_option(self, interaction):
        """Process trivia answers"""
        if not interaction.custom_id == "trivia":
            return
        async with self.bot.pool.acquire() as db:
            if await db.fetchval("SELECT TRUE FROM trivia WHERE id = $1 AND member = $2", interaction.message.id, interaction.user.id):
                await interaction.respond(content="You have already answered this question, press the info button to see your answer")
                return
            answer = interaction.raw_data["d"]["data"]["values"][0]
            await db.execute("INSERT INTO trivia (id, guild, member, correct, answer) VALUES ($1, $2, $3, $4, $5)",
                             interaction.message.id, interaction.guild.id, interaction.user.id, answer[0] == "+", answer[1:])
            if answer[0] == "+":
                await interaction.respond(content=f"`{answer[1:]}` is the correct answer!")
            else:
                await interaction.respond(content=f"`{answer[1:]}` is not the correct answer :(")

    @commands.Cog.listener()
    async def on_button_click(self, interaction):
        """Give info about trivia question when info button pushed"""
        if not interaction.custom_id.startswith("trivia"):
            return
        if interaction.custom_id == "trivia.info":
            async with self.bot.pool.acquire() as db:
                answer = await db.fetchrow("SELECT answer, correct FROM trivia WHERE id = $1 AND member = $2", interaction.message.id, interaction.user.id)
                if answer is None:
                    await interaction.respond(content="You have not submitted an answer yet!")
                    return
                info = await db.fetchrow("SELECT COUNT(CASE correct WHEN TRUE THEN 1 END) as correct, COUNT(*) AS total FROM trivia WHERE id = $1", interaction.message.id)
            await interaction.respond(content=f"Your answer was {'correct' if answer['correct'] else 'incorrect'}: `{answer['answer']}`\n"
                                      f"Out of {info['total']} who answered, {info['correct']} answered correctly ({info['correct']/info['total'] * 100:.1f}%)")
        else:
            raise NameError(f"No handler writen for {interaction.custom_id!r}")


def setup(bot):
    """
    Load extension
    """
    bot.add_cog(Fun(bot))
