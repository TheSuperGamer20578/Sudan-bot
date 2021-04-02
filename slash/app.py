from os import getenv

from flask import Flask, jsonify, request, Response, abort
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()
BLUE = 0x0a8cf0
PURPLE = 0x6556FF
GREEN = 0x36eb45
RED = 0xb00e0e
commands = {}


def command(func):
    commands[func.__name__] = func
    return func


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
        return commands[request.json["data"]["name"]](request.json)


@command
def ping(ctx):
    return jsonify({
        "type": 4,
        "data": {
            "content": "Pong!"
        }
    })


@command
def invite(ctx):
    return jsonify({
        "type": 4,
        "data": {
            "embeds": [{
                "title": "Add me to your own server by clicking here",
                "url": "https://discord.com/api/oauth2/authorize?client_id=693313847028744212&permissions=0&scope=bot%20applications.commands",
                "color": BLUE
            }]
        }
    })


@command
def github(ctx):
    return jsonify({
        "type": 4,
        "data": {
            "embeds": [{
                "title": "Click here to goto my Github repository",
                "url": "https://github.com/TheSuperGamer20578/Sudan-bot",
                "color": BLUE
            }]
        }
    })
