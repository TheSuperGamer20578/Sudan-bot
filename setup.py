from os import getenv

from requests import post
from dotenv import load_dotenv

load_dotenv()
DISCORD = f"https://discord.com/api/v8/applications/{getenv('APPLICATION_ID')}"
HEADERS = {"Authorization": f"Bot {getenv('BOT_TOKEN')}"}

post(DISCORD+"/commands", headers=HEADERS, json={
    "name": "ping",
    "description": "Ping! Pong!"
})

post(DISCORD+"/commands", headers=HEADERS, json={
    "name": "invite",
    "description": "Invite me to your own server"
})

post(DISCORD+"/commands", headers=HEADERS, json={
    "name": "github",
    "description": "Get a link to my Github repository"
})

post(DISCORD+"/commands", headers=HEADERS, json={
    "name": "town",
    "description": "Gets info about a town",
    "options": [{
        "name": "town",
        "description": "The name of the town you want info about",
        "type": 3,
        "required": True
    }]
})

post(DISCORD+"/commands", headers=HEADERS, json={
    "name": "nation",
    "description": "Gets info about a nation",
    "options": [{
        "name": "nation",
        "description": "The name of the nation you want info about",
        "type": 3,
        "required": True
    }]
})

post(DISCORD+"/commands", headers=HEADERS, json={
    "name": "resident",
    "description": "Gets info about a player",
    "options": [{
        "name": "player",
        "description": "The name of the player you want info about",
        "type": 3,
        "required": True
    }]
})
