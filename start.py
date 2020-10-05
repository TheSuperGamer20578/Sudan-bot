"""
A start script to start the bot with a ui it is very useless so use core.py or start.sh instead if you really want to use this you will need to install termcolor
"""
import os
import threading
import configparser
from discord.ext import commands, tasks
from termcolor import cprint

config = configparser.ConfigParser()
config.read("Config/config.ini")
bot = None


def clear():
    """
    Clear command
    """
    os.system("cls")


def start():
    """
    Start menu
    """
    global bot
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
        bot = commands.Bot(command_prefix="&")
        bot.load_extension("core")
        with open("Config/cogs.txt", "r") as f:
            for x in f.read().split("\n"):
                if x != "":
                    bot.load_extension(x)
        x = threading.Thread(target=loop)
        x.start()

        @tasks.loop(seconds=1)
        async def loops():
            """
            Checks to see if the stop command has been executed
            """
            if "stop" in os.listdir():
                while "stop" in os.listdir():
                    os.remove("stop")
                await bot.logout()

        @bot.event
        async def on_ready():
            """
            Starts the loop when the bot has started
            """
            loops.start()

        bot.run(config["api"]["discord"])
    elif command == "exit":
        pass
    elif command == "safe":
        x = threading.Thread(target=loop)
        x.start()
        bot = commands.Bot(command_prefix="&")
        bot.run(config["api"]["discord"])
    else:
        input("INVALID COMMAND")
        return start()


def loop():
    """
    The loop
    """
    global bot
    if bot is None:
        # this is here only for the purpose of making pycharm happy
        bot = commands.Bot(command_prefix="&")
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
        bot.load_extension(command.split(" ")[1])
    elif command.split(" ")[0] == "unload":
        bot.unload_extension(command.split(" ")[1])
    elif command == "list":
        for x in bot.cogs:
            cprint(x, "GREEN")
        for x in os.listdir():
            if x.endswith(".py") and x[:-3] not in bot.cogs and x != "start.py":
                cprint(x[:-3], "RED")
    else:
        print("Unknown command")
    input("\n\nPress enter to continue")
    return loop()


start()
