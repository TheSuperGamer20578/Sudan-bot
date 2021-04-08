from os import getenv, environ

from flask import Flask, jsonify, request, Response, abort
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from dotenv import load_dotenv
from emc import Town, Nation, Resident
from emc.exceptions import TownNotFoundException, NationNotFoundException
from psycopg2 import connect

app = Flask(__name__)
load_dotenv()
if "DATABASE_URL" in environ:
    db = connect(getenv("DATABASE_URL"))
else:
    db = connect(user=os.getenv("DB_USERNAME"), password=os.getenv("DB_PASSWORD"),
                 host=os.getenv("DB_HOST"), database=os.getenv("DB_DATABASE"))
BLUE = 0x0a8cf0
PURPLE = 0x6556FF
GREEN = 0x36eb45
RED = 0xb00e0e
commands = {}


class Checks:
    @staticmethod
    def admin(ctx):
        with db.cursor() as curr:
            curr.execute("SELECT admin_roles FROM guilds WHERE id = %s", (ctx["guild_id"],))
            roles = curr.fetchone()[0]
        for role in roles:
            if str(role) in ctx["member"]["roles"]:
                return True
            return False


def command(func):
    commands[func.__name__] = func
    return func


def check(check):
    def decorator(func):
        def wrapper(ctx, private):
            if check(ctx):
                return func(ctx, private)
            return {
                "flags": 64,
                "content": f"You do not have permission to use {ctx['data']['name']}"
            }
        return wrapper
    return decorator


def _long_fields(title, list_):
    all_comma_sep = ", ".join(list_)
    if len(all_comma_sep) > 1024 - 6:
        list_a = all_comma_sep[:1024 - 6].split(', ')[:-1]
        return [
            {
                "name": title,
                "value": f"```{', '.join(list_a)}```",
                "inline": False
            },
            *_long_fields("\N{zero width space}", list_[len(list_a):])
        ]
    else:
        return [{
            "name": title,
            "value": f"```{all_comma_sep}```",
            "inline": False
        }]


@app.route("/", methods=["POST"])
def slash():
    signature = request.headers["X-Signature-Ed25519"]
    timestamp = request.headers["X-Signature-Timestamp"]
    body = request.data
    verify_key = VerifyKey(bytes.fromhex(getenv("PUBLIC_KEY")))
    try:
        verify_key.verify(timestamp.encode() + body, bytes.fromhex(signature))
    except BadSignatureError:
        abort(401)
    if request.json["type"] == 1:
        return jsonify({
            "type": 1
        })
    elif request.json["type"] == 2:
        with db.cursor() as curr:
            curr.execute("SELECT private_commands FROM guilds WHERE id = %s", (int(request.json["guild_id"]),))
            private = curr.fetchone()[0]
        return jsonify({"type": 4, "data": {"flags": 64 if private else 0, **commands[request.json["data"]["name"]](request.json, private)}})


@command
def debug(ctx, private):
    return {"content": repr(ctx)}


@command
def ping(ctx, private):
    return {
        "content": "Pong!"
    }


@command
def invite(ctx, private):
    if private:
        return {"content": "[Add me to your own server by clicking here](https://discord.com/api/oauth2/authorize?client_id=693313847028744212&permissions=0&scope=bot%20applications.commands)"}
    return {
        "embeds": [{
            "title": "Add me to your own server by clicking here",
            "url": "https://discord.com/api/oauth2/authorize?client_id=693313847028744212&permissions=0&scope=bot%20applications.commands",
            "color": BLUE
        }]
    }


@command
def github(ctx, private):
    if private:
        return {"content": "[Click here to goto my Github repository](https://github.com/TheSuperGamer20578/Sudan-bot)"}
    return {
        "embeds": [{
            "title": "Click here to goto my Github repository",
            "url": "https://github.com/TheSuperGamer20578/Sudan-bot",
            "color": BLUE
        }]
    }


@command
def town(ctx, private):
    try:
        town = Town(ctx["data"]["options"][0]["value"])
    except TownNotFoundException:
        return {
            "flags": 64,
            "content": f"The town {ctx['data']['options'][0]['value']} was not found"
            # "embeds": [{
            #     "title": f"The town {ctx['data']['options'][0]['value']} was not found",
            #     "color": RED
            # }]
        }
    if private:
        online = [res.name for res in town.residents if res.online]
        return {"content": f"""```md
### {town} ###
<Mayor> {town.mayor}
<Nation> {town.nation}
<Residents {len(town.residents)}> {', '.join([res.name for res in town.residents])}
<Online {len(online)}> {', '.join(online) if len(online) > 0 else f'No residents online in {town}'}
()[Flags]()
{'#' if town.flags['capital'] else '>'} Capital
{'#' if town.flags['fire'] else '>'} Fire
{'#' if town.flags['explosions'] else '>'} Explosions
{'#' if town.flags['mobs'] else '>'} Mobs
{'#' if town.flags['pvp'] else '>'} PVP```"""}
    embed = {
        "title": town.name,
        "color": int(town.colour[1:], 16),
        "fields": [
            {
                "name": "Mayor",
                "value": f"```{town.mayor}```",
                "inline": True
            },
            {
                "name": "Nation",
                "value": f"```{town.nation}```",
                "inline": True
            },
            {
                "name": "Flags",
                "value": f"""```diff
{'+' if town.flags['capital'] else '-'} Capital
{'+' if town.flags['fire'] else '-'} Fire
{'+' if town.flags['explosions'] else '-'} Explosions
{'+' if town.flags['mobs'] else '-'} Mobs
{'+' if town.flags['pvp'] else '-'} PVP
```""",
                "inline": True
            },
            *_long_fields(f"Residents [{len(town.residents)}]",
                          [res.name for res in town.residents])
        ]
    }
    online = [res.name for res in town.residents if res.online]
    if len(online) > 0:
        embed["fields"].append({
            "name": f"Online residents [{len(online)}]",
            "value": f"```{', '.join(online)}```",
            "inline": False
        })
    else:
        embed["fields"].append({
            "name": "Online residents [0]",
            "value": f"```No online residents in {town}```",
            "inline": False
        })
    return {"embeds": [embed]}


@command
def nation(ctx, private):
    try:
        nation = Nation(ctx["data"]["options"][0]["value"])
    except NationNotFoundException:
        return {
            "flags": 64,
            "content": f"The nation {ctx['data']['options'][0]['value']} was not found"
            # "embeds": [{
            #     "title": f"The nation {ctx['data']['options'][0]['value']} was not found",
            #     "color": RED
            # }]
        }
    if private:
        online = [res.name for res in nation.citizens if res.online]
        return {"content": f"""```md
### {nation} ###
<Leader> {nation.leader}
<Capital> {nation.capital}
<Population> {len(nation.citizens)}
<Towns {len(nation.towns)}> {', '.join([town.name for town in nation.towns])}
<Online {len(online)}> {', '.join(online) if len(online) > 0 else f'No citizens online in {nation}'}```"""}
    embed = {
        "title": nation.name,
        "color": int(nation.colour[1:], 16),
        "fields": [
            {
                "name": "Leader",
                "value": f"```{nation.leader}```",
                "inline": True
            },
            {
                "name": "Capital",
                "value": f"```{nation.capital}```",
                "inline": True
            },
            {
                "name": "Population",
                "value": f"```{len(nation.citizens)}```",
                "inline": True
            },
            *_long_fields(f"Towns [{len(nation.towns)}]",
                          [town.name for town in nation.towns])
        ]
    }
    online = [res.name for res in nation.citizens if res.online]
    if len(online) > 0:
        embed["fields"].append({
            "name": f"Online [{len(online)}]",
            "value": f"```{', '.join(online)}```",
            "inline": False
        })
    else:
        embed["fields"].append({
            "name": "Online [0]",
            "value": f"```No citizens online in {nation}```",
            "inline": False
        })
    return {"embeds": [embed]}


@command
def resident(ctx, private):
    resident = Resident(ctx["data"]["options"][0]["value"])
    if private:
        resp = f"""```md
### {resident} ###
<Town> {resident.town}
<Nation> {resident.nation}
<Position> """
        if resident.online:
            if resident.hidden:
                resp += f"{resident} is currently not visible on the map```"
            else:
                resp += f"{resident.position[0]}/{resident.position[1]}/{resident.position[2]}```([map]({emc.util.map_link(resident.position)}))"
        else:
            resp += f"{resident} is currently offline```"
        return {"content": resp}
    embed = {
        "title": resident.name,
        "color": BLUE,
        "thumbnail": {
            "url": f"https://minotar.net/armor/bust/{resident}"
        },
        "fields": [
            {
                "name": "Town",
                "value": f"```{resident.town}```",
                "inline": True
            },
            {
                "name": "Nation",
                "value": f"```{resident.nation}```",
                "inline": True
            }
        ]
    }
    if resident.online:
        if resident.hidden:
            embed["fields"].append({
                "name": "Position",
                "value": f"```{resident} is currently not visible on the map```",
                "inline": True
            })
        else:
            embed["fields"].append({
                "name": "Position",
                "value": f"```{resident.position[0]}/{resident.position[1]}/{resident.position[2]}```([map]({emc.util.map_link(resident.position)}))",
                "inline": True
            })
    else:
        embed["fields"].append({
            "name": "Position",
            "value": f"```{resident} is currently offline```",
            "inline": True
        })
    return {"embeds": [embed]}


@command
def settings(ctx, private):
    if private:
        message = "### Settings ###"
        if Checks.admin(ctx):
            with db.cursor() as curr:
                curr.execute(
                    "SELECT admin_roles, mod_roles, support_roles, chain_break_role, private_commands FROM guilds WHERE id = %s",
                    (ctx["guild_id"],))
                settings = curr.fetchone()
            message += f"""
--- Server settings ---
Admin roles: {', '.join([f'<@&{role}>' for role in settings[0]]) if len(settings[0]) > 0 else 'None'}
Moderator roles: {', '.join([f'<@&{role}>' for role in settings[1]]) if len(settings[1]) > 0 else 'None'}
Ticket support roles: {', '.join([f'<@&{role}>' for role in settings[2]]) if len(settings[2]) > 0 else 'None'}
Chain break role: {f'<@&{settings[3]}>' if settings[3] is not None else 'None'}
Private commands: {'🟢' if settings[4] else '🔴'}"""
        with db.cursor() as curr:
            curr.execute("SELECT dad_mode FROM users WHERE id = %s",
                         (ctx["member"]["user"]["id"],))
            settings = curr.fetchone()
        message += f"""
--- User settings ---
Dad mode: {'🟢' if settings[0] else '🔴'}"""
        return {"content": message}
    embed = {
        "title": "Settings",
        "color": BLUE,
        "fields": []
    }
    if Checks.admin(ctx):
        with db.cursor() as curr:
            curr.execute("SELECT admin_roles, mod_roles, support_roles, chain_break_role, private_commands FROM guilds WHERE id = %s", (ctx["guild_id"],))
            settings = curr.fetchone()
        embed["fields"].append({
            "name": "Server settings",
            "value": f"""
                Admin roles: {', '.join([f'<@&{role}>' for role in settings[0]]) if len(settings[0]) > 0 else 'None'}
                Moderator roles: {', '.join([f'<@&{role}>' for role in settings[1]]) if len(settings[1]) > 0 else 'None'}
                Ticket support roles: {', '.join([f'<@&{role}>' for role in settings[2]]) if len(settings[2]) > 0 else 'None'}
                Chain break role: {f'<@&{settings[3]}>' if settings[3] is not None else 'None'}
                Private commands: {'🟢' if settings[4] else '🔴'}
            """
        })
    with db.cursor() as curr:
        curr.execute("SELECT dad_mode FROM users WHERE id = %s", (ctx["member"]["user"]["id"],))
        settings = curr.fetchone()
    embed["fields"].append({
        "name": "User settings",
        "value": f"""
            Dad mode: {'🟢' if settings[0] else '🔴'}
        """
    })
    return {"embeds": [embed]}


@command
def set(ctx, private):
    if ctx["data"]["options"][0]["name"] == "user":
        if ctx["data"]["options"][0]["options"][0]["name"] == "dadmode":
            with db.cursor() as curr:
                curr.execute("UPDATE users SET dad_mode = %s WHERE id = %s",
                    (
                        ctx["data"]["options"][0]["options"][0]["options"][0]["value"],
                        int(ctx["member"]["user"]["id"])
                    ))
            if private:
                return {"content": f"{'Enabled' if toggle else 'Disabled'} dad mode"}
            return {
                "embeds": [{
                    "title": "Settings updated",
                    "description": f"{'Enabled' if toggle else 'Disabled'} dad mode",
                    "color": GREEN
                }]
            }

    elif ctx["data"]["options"]["name"] == "server":
        if not Checks.admin(ctx):
            return {"flags": 64, "content": "You do not have permission to change server settings"}
        pass
