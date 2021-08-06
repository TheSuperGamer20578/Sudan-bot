"""
Stuff that is shared between all cogs
"""
# colours
BLUE = 0x0a8cf0
PURPLE = 0x6556FF
GREEN = 0x36eb45
RED = 0xb00e0e


class Checks:
    """
    Permission checks
    """
    @staticmethod
    async def trusted(ctx, bot=None):
        """
        Check to see if the user is trusted
        """
        async with (bot if bot is not None else ctx.bot).pool.acquire() as db:
            return await db.fetchval("SELECT trusted FROM users WHERE id = $1", ctx.author.id)

    @staticmethod
    async def mod(ctx, bot=None):
        """
        Check to see if the user is a mod
        """
        async with (bot if bot is not None else ctx.bot).pool.acquire() as db:
            for role in await db.fetchval("SELECT mod_roles FROM guilds WHERE id = $1", ctx.guild.id):
                if role in [r.id for r in ctx.author.roles]:
                    return True
            return False

    @staticmethod
    async def admin(ctx, bot=None):
        """
        Check to see if the user is an admin
        """
        async with (bot if bot is not None else ctx.bot).pool.acquire() as db:
            for role in await db.fetchval("SELECT admin_roles FROM guilds WHERE id = $1", ctx.guild.id):
                if role in [r.id for r in ctx.author.roles]:
                    return True
            return False

    @staticmethod
    async def slash(ctx, bot=None):
        """
        Check to see if command has slash command alternative
        """
        async with (bot if bot is not None else ctx.bot).pool.acquire() as db:
            return not await db.fetchval("SELECT force_slash FROM guilds WHERE id = $1", ctx.guild.id)
