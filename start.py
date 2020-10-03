import discord
import os
import threading
from discord.ext import commands, tasks
from termcolor import cprint
from Config import apikeys
bot = None


def clear():
    os.system("cls")


# noinspection SpellCheckingInspection
def start():
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
            if "stop" in os.listdir():
                while "stop" in os.listdir():
                    os.remove("stop")
                await bot.logout()

        @bot.event
        async def on_ready():
            loops.start()

        bot.run(apikeys.discord)
    elif command == "exit":
        pass
    elif command == "safe":
        x = threading.Thread(target=loop)
        x.start()
        bot = commands.Bot(command_prefix="&")
        bot.run(apikeys.discord)
    else:
        input("INVALID COMMAND")
        return start()


def loop():
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
            cprint(x, "green")
        for x in os.listdir():
            if x.endswith(".py") and x[:-3] not in bot.cogs and x != "start.py":
                cprint(x[:-3], "red")
    else:
        print("Unknown command")
    input("\n\nPress enter to continue")
    return loop()


start()
