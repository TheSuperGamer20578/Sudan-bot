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
    db = connect(getenv("DATABASE_URL"), ssl="require")
else:
    db = connect(user=os.getenv("DB_USERNAME"), password=os.getenv("DB_PASSWORD"),
                 host=os.getenv("DB_HOST"), database=os.getenv("DB_DATABASE"))
BLUE = 0x0a8cf0
PURPLE = 0x6556FF
GREEN = 0x36eb45
RED = 0xb00e0e
commands = {}


def command(func):
    commands[func.__name__] = func
    return func


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
            curr.execute("SELECT private_commands FROM guilds WHERE id = %s", (int(request.json["guild_id"])))
            private = curr.fetchone()[0]
            return jsonify({"flags": 64 if private else 0, "type": 4, **commands[request.json["data"]["name"]](request.json)})


@command
def ping(ctx):
    return {
        "data": {
            "content": "Pong!"
        }
    }


@command
def invite(ctx):
    return {
        "data": {
            "embeds": [{
                "title": "Add me to your own server by clicking here",
                "url": "https://discord.com/api/oauth2/authorize?client_id=693313847028744212&permissions=0&scope=bot%20applications.commands",
                "color": BLUE
            }]
        }
    }


@command
def github(ctx):
    return {
        "data": {
            "embeds": [{
                "title": "Click here to goto my Github repository",
                "url": "https://github.com/TheSuperGamer20578/Sudan-bot",
                "color": BLUE
            }]
        }
    }


@command
def town(ctx):
    try:
        town = Town(ctx["data"]["options"][0]["value"])
    except TownNotFoundException:
        return {
            "flags": 64,
            "data": {
                "embeds": [{
                    "title": f"The town {ctx['data']['options'][0]['value']} was not found",
                    "color": RED
                }]
            }
        }
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
    return {
        "data": {
            "embeds": [embed]
        }
    }


@command
def nation(ctx):
    try:
        nation = Nation(ctx["data"]["options"][0]["value"])
    except NationNotFoundException:

        return {
            "flags": 64,
            "data": {
                "embeds": [{
                    "title": f"The nation {ctx['data']['options'][0]['value']} was not found",
                    "color": RED
                }]
            }
        }
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
            "value": f"```0 citizens online in {nation}```",
            "inline": False
        })
    return {
        "data": {
            "embeds": [embed]
        }
    }


@command
def resident(ctx):
    resident = Resident(ctx["data"]["options"][0]["value"])
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
    return {
        "data": {
            "embeds": [embed]
        }
    }
