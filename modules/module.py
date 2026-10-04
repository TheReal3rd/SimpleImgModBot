
from discord import app_commands
from discord.ext import commands, tasks


class ModuleBase():

    def __init__(self, name:str, description:str, client:commands.Bot) -> None:
        self._name = name
        self._description = description
        self._client = client

    def getName(self) -> str:
        return self._name

    def getDescription(self) -> str:
        return self._description



