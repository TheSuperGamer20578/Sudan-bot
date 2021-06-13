"""
Stuff that is shared between all cogs
"""
# colours
BLUE = 0x0a8cf0
PURPLE = 0x6556FF
GREEN = 0x36eb45
RED = 0xb00e0e

_DB = None


def set_db(database):
    """
    Sets the db
    """
    global _DB  # pylint: disable=global-statement
    _DB = database


class Checks:
    """
    Permission checks
    """

    @staticmethod
    async def trusted(ctx):
        """
        Check to see if the user is trusted
        """
        return await _DB.fetchval(
            "SELECT trusted FROM users WHERE id = $1",
            ctx.author.id)

    @staticmethod
    async def mod(ctx):
        """
        Check to see if the user is a mod
        """
        for role in await _DB.fetchval("SELECT mod_roles FROM guilds WHERE id = $1", ctx.guild.id):
            if role in [r.id for r in ctx.author.roles]:
                return True
        return False

    @staticmethod
    async def admin(ctx):
        """
        Check to see if the user is an admin
        """
        for role in await _DB.fetchval("SELECT admin_roles FROM guilds WHERE id = $1", ctx.guild.id):
            if role in [r.id for r in ctx.author.roles]:
                return True
        return False

    @staticmethod
    async def slash(ctx):
        """
        Check to see if command has slash command alternative
        """
        return not await _DB.fetchval("SELECT force_slash FROM guilds WHERE id = $1", ctx.guild.id)
