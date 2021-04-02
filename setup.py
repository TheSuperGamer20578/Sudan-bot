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
