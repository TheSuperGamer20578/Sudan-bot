"""Contains stuff for logging"""
from typing import Dict, TextIO
from datetime import datetime

import discord

_AVATARS: Dict[str, str] = {
    "debug": "https://cdn.discordapp.com/embed/avatars/1.png",
    "info": "https://cdn.discordapp.com/embed/avatars/0.png",
    "warning": "https://cdn.discordapp.com/embed/avatars/3.png",
    "error": "https://cdn.discordapp.com/embed/avatars/4.png",
    "log": "https://cdn.discordapp.com/embed/avatars/2.png"
}
LEVELS: Dict[str, int] = {
    "none": 0,
    "error": 1,
    "warning": 2,
    "info": 3,
    "debug": 4
}
LEVELS_FROM_INT: Dict[int, str] = {
    0: "none",
    1: "error",
    2: "warning",
    3: "info",
    4: "debug"
}


class Logger:
    """Class for logging stuff"""
    _log_hook: discord.Webhook
    _error: discord.Webhook
    _public: discord.TextChannel
    _level: int = 2
    _file: TextIO
    _name: str

    def __init__(self, log_webhook: discord.Webhook, error_webhook: discord.Webhook, public_log_channel: discord.TextChannel, file: TextIO, name: str):
        self._log_hook = log_webhook
        self._error = error_webhook
        self._public = public_log_channel
        self._file = file
        self._name = name

    async def _log(self, avatar: str, level: str, text: str, destination: discord.abc.Messageable):
        if isinstance(destination, discord.Webhook):
            await destination.send(text, avatar_url=avatar, username=f"[{level}] {self._name}")
        else:
            await destination.send(discord.Embed(title=text))
        if destination == self._log_hook:
            self._file.write(f"{datetime.now():%d/%m/%Y %H:%M:%S} [{level}] {text}\n")
            self._file.flush()

    async def change_level(self, level: int, user: str):
        """Changes the log level"""
        assert 0 <= level <= 4
        self._level = level
        await self._log(_AVATARS["log"], "LOG UPDATE", f"{user} has changed the log level to {LEVELS_FROM_INT[level]}", self._log_hook)

    async def debug(self, message: str):
        """Logs debug"""
        if self._level >= LEVELS["debug"]:
            await self._log(_AVATARS["debug"], "DEBUG", message, self._log_hook)

    async def info(self, message: str):
        """Logs info"""
        if self._level >= LEVELS["info"]:
            await self._log(_AVATARS["info"], "INFO", message, self._log_hook)

    async def warning(self, message: str):
        """Logs a warning"""
        if self._level >= LEVELS["warning"]:
            await self._log(_AVATARS["warning"], "WARNING", message, self._log_hook)

    async def error(self, message: str):
        """Logs an error"""
        if self._level >= LEVELS["error"]:
            await self._log(_AVATARS["error"], "ERROR", message, self._log_hook)

    async def exception(self, message: str):
        """Logs an error to the errors channel"""
        await self._log(_AVATARS["error"], "EXCEPTION", message, self._error)

    async def public(self, message: str):
        """Sends a message to the public logs"""
        await self._log(None, None, message, self._public)
