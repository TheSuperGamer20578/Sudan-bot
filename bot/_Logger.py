"""Contains stuff for logging"""
from typing import Dict, List, TextIO
from datetime import datetime

import discord
from discord.ext.tasks import loop

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
    _stdout: List[str] = []
    _stderr: List[str] = []

    def __init__(self, log_webhook: discord.Webhook, error_webhook: discord.Webhook, public_log_channel: discord.TextChannel, file: TextIO, name: str):
        self._log_hook = log_webhook
        self._error = error_webhook
        self._public = public_log_channel
        self._file = file
        self._name = name
        self._log_cached.start()  # pylint: disable=no-member

    async def _log(self, avatar: str, level: str, text: str, destination: discord.abc.Messageable):
        if isinstance(destination, discord.Webhook):
            await destination.send(text, avatar_url=avatar, username=f"[{level}] {self._name}")
        else:
            await destination.send(embed=discord.Embed(title=text))
        if destination == self._log_hook:
            self._file.write(f"{datetime.now():%d/%m/%Y %H:%M:%S} [{level}] {text}\n")
            self._file.flush()

    @loop(seconds=5)
    async def _log_cached(self):
        if len(self._stderr) > 0:
            await self._log_hook.send("\n".join(self._stderr[:100]), avatar_url=_AVATARS["error"], username=f"[STDERR] {self._name}")
            del self._stderr[:100]
        if len(self._stdout) > 0:
            await self._log_hook.send("\n".join(self._stdout[:100]), avatar_url=_AVATARS["info"], username=f"[STDOUT] {self._name}")
            del self._stdout[:100]

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

    def stdout(self, message: str):
        """Log info after caching"""
        self._file.write(f"{datetime.now():%d/%m/%Y %H:%M:%S} [STDOUT] {message}\n")
        self._file.flush()
        self._stdout.append(message)

    def stderr(self, message: str):
        """Log error after caching"""
        self._file.write(f"{datetime.now():%d/%m/%Y %H:%M:%S} [STDERR] {message}\n")
        self._file.flush()
        self._stderr.append(message)
