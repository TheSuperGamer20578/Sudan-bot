from os import getenv
from time import sleep

from requests import post
from dotenv import load_dotenv

load_dotenv()
DISCORD = f"https://discord.com/api/v8/applications/{getenv('APPLICATION_ID')}"
HEADERS = {"Authorization": f"Bot {getenv('BOT_TOKEN')}"}
DELAY = 3

post(DISCORD + "/commands", headers=HEADERS, json={
    "name": "ping",
    "description": "Ping! Pong!"
})
sleep(DELAY)

post(DISCORD + "/commands", headers=HEADERS, json={
    "name": "invite",
    "description": "Invite me to your own server"
})
sleep(DELAY)

post(DISCORD + "/commands", headers=HEADERS, json={
    "name": "github",
    "description": "Get a link to my Github repository"
})
sleep(DELAY)

post(DISCORD + "/commands", headers=HEADERS, json={
    "name": "town",
    "description": "Gets info about a town",
    "options": [{
        "name": "town",
        "description": "The name of the town you want info about",
        "type": 3,
        "required": True
    }]
})
sleep(DELAY)

post(DISCORD + "/commands", headers=HEADERS, json={
    "name": "nation",
    "description": "Gets info about a nation",
    "options": [{
        "name": "nation",
        "description": "The name of the nation you want info about",
        "type": 3,
        "required": True
    }]
})
sleep(DELAY)

post(DISCORD + "/commands", headers=HEADERS, json={
    "name": "resident",
    "description": "Gets info about a player",
    "options": [{
        "name": "player",
        "description": "The name of the player you want info about",
        "type": 3,
        "required": True
    }]
})
sleep(DELAY)

post(DISCORD + "/commands", headers=HEADERS, json={
    "name": "settings",
    "description": "Shows your settings"
})
sleep(DELAY)

post(DISCORD + "/commands", headers=HEADERS, json={
    "name": "set",
    "description": "Changes settings",
    "options": [
        {
            "type": 2,
            "name": "user",
            "description": "Changes user settings",
            "options": [
                {
                    "type": 1,
                    "name": "dadmode",
                    "description": "Enables or disables dad mode",
                    "options": [
                        {
                            "type": 5,
                            "name": "value",
                            "description": "Value to set dad mode to",
                            "required": True
                        }
                    ]
                }
            ]
        },
        {
            "type": 2,
            "name": "server",
            "description": "Changes server settings",
            "options": [
                {
                    "type": 1,
                    "name": "chainbreak",
                    "description": "Set the role to be assigned to whoever breaks a chain",
                    "options": [
                        {
                            "type": 8,
                            "name": "role",
                            "description": "The role to be assigned to whoever breaks a chain",
                            "required": True
                        }
                    ]
                },
                {
                    "type": 1,
                    "name": "admin",
                    "description": "Add or remove an admin role",
                    "options": [
                        {
                            "type": 4,
                            "name": "operation",
                            "description": "Add or remove from admin roles",
                            "required": True,
                            "choices": [
                                {
                                    "name": "add",
                                    "value": 1
                                },
                                {
                                    "name": "remove",
                                    "value": 0
                                }
                            ]
                        },
                        {
                            "type": 8,
                            "name": "role",
                            "description": "Role to add or remove from admin roles",
                            "required": True
                        }
                    ]
                },
                {
                    "type": 1,
                    "name": "moderator",
                    "description": "Add or remove a moderator role",
                    "options": [
                        {
                            "type": 4,
                            "name": "operation",
                            "description": "Add or remove from moderator roles",
                            "required": True,
                            "choices": [
                                {
                                    "name": "add",
                                    "value": 1
                                },
                                {
                                    "name": "remove",
                                    "value": 0
                                }
                            ]
                        },
                        {
                            "type": 8,
                            "name": "role",
                            "description": "Role to add or remove from moderator roles",
                            "required": True
                        }
                    ]
                },
                {
                    "type": 1,
                    "name": "ticketsupport",
                    "description": "Add or remove a ticket support role",
                    "options": [
                        {
                            "type": 4,
                            "name": "operation",
                            "description": "Add or remove from ticket support roles",
                            "required": True,
                            "choices": [
                                {
                                    "name": "add",
                                    "value": 1
                                },
                                {
                                    "name": "remove",
                                    "value": 0
                                }
                            ]
                        },
                        {
                            "type": 8,
                            "name": "role",
                            "description": "Role to add or remove from ticket support roles",
                            "required": True
                        }
                    ]
                },
                {
                    "type": 1,
                    "name": "privatecommands",
                    "description": "Set if slash command response should only show to the invoker",
                    "options": [
                        {
                            "type": 5,
                            "name": "value",
                            "description": "Value to set private commands to",
                            "required": True
                        }
                    ]
                }
            ]
        }
    ]
})
sleep(DELAY)
