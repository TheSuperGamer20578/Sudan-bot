import discord
from discord.ext import commands
import firebase_admin
from firebase_admin import *
from firebase_admin import firestore
last_chain = {}
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase.json")
    initialize_app(cred)
db = firestore.client()
fs_data = db.collection("fun")
settings = db.collection("settings")

class fun(commands.Cog):
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
        d = fs_data.document(str(ctx.guild.id)).get().to_dict()
        if str(ctx.channel.id) in d["chain"]:
            return
        if d is None:
            d = {"chain": {}}
        d["chain"][str(ctx.channel.id)] = thing
        last_chain[str(ctx.channel.id)] = None
        fs_data.document(str(ctx.guild.id)).set(d)
        if thing.startswith("$counting:"):
            await ctx.send(f"Counting started at: {thing.split(':')[1]}")
        else:
            await ctx.send(f"New chain: {thing}")

    @commands.Cog.listener()
    async def on_message(self, msg):
        async def cbreak():
            if msg.content[1:] == f"chain {d['chain'][str(msg.channel.id)]}":
                return
            await msg.channel.send(f"{msg.author.mention} broke the chain! start a new chain with `.chain <thing>`")
            s = settings.document(str(msg.guild.id)).get().to_dict()
            if "breakrole" in s:
                await msg.author.add_roles(msg.guild.get_role(int(s["breakrole"])))
            del d["chain"][str(msg.channel.id)]
            fs_data.document(str(msg.guild.id)).set(d)
        d = fs_data.document(str(msg.guild.id)).get().to_dict()
        if d is None or msg.author.bot:
            return
        if str(msg.channel.id) in d["chain"]:
            if d["chain"][str(msg.channel.id)].startswith("$counting:"):
                num = int(d["chain"][str(msg.channel.id)].split(":")[1])
                if msg.content != str(num+1):
                    await cbreak()
                else:
                    num += 1
                    d["chain"][str(msg.channel.id)] = f"$counting:{num}"
                    fs_data.document(str(msg.guild.id)).set(d)
            elif msg.content != d["chain"][str(msg.channel.id)] or msg.author.id == last_chain[str(msg.channel.id)]:
                await cbreak()
            else:
                last_chain[str(msg.channel.id)] = msg.author.id


def setup(bot):
    bot.add_cog(fun(bot))
