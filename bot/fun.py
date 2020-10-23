"""
Contains fun stuff
"""
import re

import discord
from discord.ext import commands
from firebase_admin import firestore, credentials, initialize_app

last_chain = {}

try:
    cred = credentials.Certificate("Config/firebase.json")
    initialize_app(cred)
except ValueError:
    pass
db = firestore.client()
fs_data = db.collection("fun")
settings = db.collection("settings")


class fun(commands.Cog):
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
        embed = discord.Embed(title=query, url=f"https://lmgtfy.com/?q={query.replace(' ', '%20')}&pp=1&iie=1")
        embed.set_author(name=ctx.author.nick, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.check(lambda ctx: "sudont" not in [role.name for role in ctx.author.roles])
    async def sudo(self, ctx, user: discord.Member, *, message):
        """
        Mimics another user
        """
        await ctx.message.delete()
        webhook = await ctx.channel.create_webhook(name=user.nick if user.nick is not None else user.name)
        await webhook.send(message.replace("@", "@\N{zero width space}"), avatar_url=user.avatar_url)
        await webhook.delete()

    @commands.command()
    async def chain(self, ctx, *, thing):
        """
        Starts a chain
        """
        if "@" in thing:
            return await ctx.send("Nice try but you cant fool me into mentioning")
        data = fs_data.document(str(ctx.guild.id)).get().to_dict()
        if str(ctx.channel.id) in data["chain"]:
            return
        if data is None:
            data = {"chain": {}}
        data["chain"][str(ctx.channel.id)] = thing
        last_chain[str(ctx.channel.id)] = None
        fs_data.document(str(ctx.guild.id)).set(data)
        if thing.startswith("$counting:"):
            await ctx.send(f"Counting started at: {thing.split(':')[1]}")
        else:
            await ctx.send(f"New chain: {thing}")

    @commands.Cog.listener()
    async def on_message(self, msg):
        """
        Checks to see if chain is broken
        """
        async def cbreak():
            """
            If the chain is broken say so and update DB
            """
            if msg.content[1:] == f"chain {data['chain'][str(msg.channel.id)]}":
                return
            await msg.add_reaction("❌")
            await msg.channel.send(f"{msg.author.mention} broke the chain! start a new chain with `.chain <thing>`")
            setting = settings.document(str(msg.guild.id)).get().to_dict()
            if "breakrole" in setting:
                await msg.author.add_roles(msg.guild.get_role(int(setting["breakrole"])))
            del data["chain"][str(msg.channel.id)]
            fs_data.document(str(msg.guild.id)).set(data)
        data = fs_data.document(str(msg.guild.id)).get().to_dict()
        if data is None or msg.author.bot:
            return
        if str(msg.channel.id) in data["chain"]:
            if data["chain"][str(msg.channel.id)].startswith("$counting:"):
                num = int(data["chain"][str(msg.channel.id)].split(":")[1])
                if msg.content != str(num+1):
                    await cbreak()
                else:
                    num += 1
                    data["chain"][str(msg.channel.id)] = f"$counting:{num}"
                    fs_data.document(str(msg.guild.id)).set(data)
            elif msg.content != data["chain"][str(msg.channel.id)] or msg.author.id == last_chain[str(msg.channel.id)]:
                await cbreak()
            else:
                last_chain[str(msg.channel.id)] = msg.author.id
                if msg.content == "100":
                    await msg.add_reaction("💯")
                else:
                    await msg.add_reaction("✅")
                           
    @commands.Cog.listener
    async def on_message(message):
        """
        dad mode
        """
        if str(message.author.id) not in fs_data.document("dad").get().to_dict():
            return
        m = re.search(r"i am (.*)", message.content.lower())
        if m:
            await message.channel.send(f"Hi {m.group(1)}! Im Dad")
                           
    @commands.command()
    async def dadmode(self, ctx):
        """
        Toggles Dad mode.
        """
        d = fs_data.document("dad").get().to_dict()
        if str(ctx.author.id) in d:
            del d[str(ctx.author,id)]
        else:
            d[str(ctx,author.id)] = True
        fs_data.document("dad").set(d)


def setup(bot):
    """
    Load extension
    """
    bot.add_cog(fun(bot))
