"""
Stuff that is shared between all cogs
"""
# colours
BLUE = 0x0a8cf0
PURPLE = 0x6556FF
GREEN = 0x36eb45
RED = 0xb00e0e


class checks:
    """
    Permission checks
    """

    def __init__(self, db):
        self.db = db

    async def trusted(self, ctx):
        """
        Check to see if the user is trusted
        """
        return await self.db.fetchval(
            "SELECT trusted FROM users WHERE id = $1",
            ctx.author.id)

    async def mod(self, ctx):
        """
        Check to see if the user is a mod
        """
        return any([a in b for a, b in (
            await self.db.fetchval(
                "SELECT mod_roles FROM guilds WHERE id = $1",
                ctx.guild.id),
            [role.id for role in ctx.author.roles])])

    async def admin(self, ctx):
        """
        Check to see if the user is an admin
        """
        return any([a in b for a, b in (
            await self.db.fetchval(
                "SELECT admin_roles FROM guilds WHERE id = $1",
                ctx.guild.id),
            [role.id for role in ctx.author.roles])])
