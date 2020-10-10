"""
Only works in a singular server and may be unstable
"""
# TODO remove this comment and the one below
# pylint: skip-file
import EMC
import discord
from discord.ext import commands


class autoroles(commands.Cog):
    """
    Automatically assigns roles
    """
    def __init__(self, bot):
        self.bot = bot
        with open("Config/allies.txt", "r") as file:
            self.allies = file.read().split("\n")

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        This is where the magic happens
        """
        if message.channel.id == 675181483199037449:
            await message.delete()
            res = EMC.Resident(message.content)
            if res.townless:
                embed = discord.Embed(title="Townless?", description=f"""
                        Are you townless?
                        If you are DM <@338865374122606616> for a town.
                        If you are not you might have entered your minecraft name wrongly.
    
                        You entered "{message.content}".
                        """)
                await message.author.send(embed=embed)
                return
            if res.town.name == "Dharug":
                await message.author.add_roles(message.guild.get_role(role_id=675187997695803443))
                await message.author.edit(nick=res.name.replace('_', ' '))
                return
            if res.town.name in self.allies:
                await message.author.add_roles(message.guild.get_role(role_id=729274541842628678))
                await message.author.edit(nick=f"{res.name.replace('_', ' ')} | {res.town.name.replace('_', ' ')}")
                if res.town.mayor == res:
                    await message.author.add_roles(message.guild.get_role(role_id=735755692409094267))
            # if res.nation.name == "Ethiopia":
            #    await message.author.add_roles(message.guild.get_role(role_id=693613984468828201))
            #    await message.author.edit(nick=f"{res.name.replace('_', ' ')} | {res.town.name.replace('_', ' ')}")
            else:
                await message.author.add_roles(message.guild.get_role(role_id=717337758779047966))
                if res.nation is not None:
                    await message.author.edit(nick=f"{res.name.replace('_', ' ')} | {res.nation.name.replace('_', ' ')}")
                else:
                    await message.author.edit(nick=f"{res.name.replace('_', ' ')}")


def setup(bot):
    """
    Load stuff so that stuff works
    """
    bot.add_cog(autoroles(bot))
