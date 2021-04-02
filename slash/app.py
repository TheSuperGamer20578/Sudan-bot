from os import getenv

from flask import Flask, jsonify, request, Response, abort
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()
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
        verify_key.verify(f"{timestamp}{body}".encode(), bytes.fromhex(signature))
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
