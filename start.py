"""
DEPRECATION WARNING: this file is deprecated and may be removed if no-one maintains it
A start script to start the bot with a ui it is very useless so use core.py or start.sh instead if you really want to use this you will need to install termcolor
"""
# pylint: skip-file
import os
import threading
import configparser
from discord.ext import commands, tasks
from termcolor import cprint

config = configparser.ConfigParser()
config.read("Config/config.ini")
BOT = None


def clear():
    """
    Clear command
    """
    os.system("cls")


def start():
    """
    Start menu
    """
    global BOT
    clear()
    print("""
        +-------------+
        |  BOT  MENU  |
        +-------------+
        OPTIONS:
            START
            EXIT
            SAFE
        
        """)
    command = input("> ")

    if command == "start":
        BOT = commands.Bot(command_prefix="&")
        BOT.load_extension("core")
        with open("Config/cogs.txt", "r") as file:
            for cog in file.read().split("\n"):
                if cog != "":
                    BOT.load_extension(cog)
        thread = threading.Thread(target=loop)
        thread.start()

        @tasks.loop(seconds=1)
        async def loops():
            """
            Checks to see if the stop command has been executed
            """
            if "stop" in os.listdir():
                while "stop" in os.listdir():
                    os.remove("stop")
                await BOT.logout()

        @BOT.event
        async def on_ready():
            """
            Starts the loop when the bot has started
            """
            loops.start()

        BOT.run(config["api"]["discord"])
    elif command == "exit":
        pass
    elif command == "safe":
        cog = threading.Thread(target=loop)
        cog.start()
        BOT = commands.Bot(command_prefix="&")
        BOT.run(config["api"]["discord"])
    else:
        input("INVALID COMMAND")
        return start()


def loop():
    """
    The loop
    """
    global BOT
    if BOT is None:
        # this is here only for the purpose of making pycharm happy
        BOT = commands.Bot(command_prefix="&")
        return
    clear()
    print("""
        +-------------+
        |  BOT  MENU  |
        +-------------+
        OPTIONS:
            STOP
            LOAD
            UNLOAD
            LIST
            
        """)
    command = input("> ")
    print("\n")
    if command == "stop":
        with open("stop", "w"):
            pass
        return start()
    elif command.split(" ")[0] == "load":
        BOT.load_extension(command.split(" ")[1])
    elif command.split(" ")[0] == "unload":
        BOT.unload_extension(command.split(" ")[1])
    elif command == "list":
        for cog in BOT.cogs:
            cprint(cog, "GREEN")
        for cog in os.listdir():
            if cog.endswith(".py") and cog[:-3] not in BOT.cogs and cog != "start.py":
                cprint(cog[:-3], "RED")
    else:
        print("Unknown command")
    input("\n\nPress enter to continue")
    return loop()


start()
