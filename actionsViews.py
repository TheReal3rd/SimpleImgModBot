
"""
Style	Enum	Appearance	Typical Use
Primary	discord.ButtonStyle.primary	Blue	Main action
Secondary	discord.ButtonStyle.secondary	Gray	Neutral actions
Success	discord.ButtonStyle.success	Green	Confirm/Accept
Danger	discord.ButtonStyle.danger	Red	Delete/Cancel
Link	discord.ButtonStyle.link	Gray (opens URL)	External links
"""

import logging
import discord
import numpy as np

from discord import app_commands
from discord.ext import commands, tasks

from discordUtils import *

logger = logging.getLogger("ClankerMod")

class BanView(discord.ui.View):

    def __init__(self, userData):
        super().__init__()
        self.userData = userData

    @discord.ui.button(label="Ban User", style=discord.ButtonStyle.danger)
    async def buttonCallback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"You clicked the button! {self.testData}", ephemeral=True)
        self.stop()


class BanImageView(discord.ui.View):

    def __init__(self, client, serverID, pendDBManager, databaseManager):
        super().__init__()
        self.client = client
        self.serverID = serverID
        self.pendingDatabaseManager = pendDBManager
        self.databaseManager = databaseManager

    @discord.ui.button(label="Ban Image", style=discord.ButtonStyle.danger)
    async def buttonCallback(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        reactMessageID = interaction.message.id
        result = self.pendingDatabaseManager.get("checks", reactMessageID)
        if result != None:

            if not user.guild_permissions.administrator:
                await interaction.response.send_message("You're not an Administrator.")
                logger.warning(f"{user.name} attempted to approve a image ban but aren't Administrator.")
                return

            offendingMessage = await getMessage(self.client, self.serverID, result["channelID"], result["messageID"])

            msg =  "Added image to banned list."
            if offendingMessage:
                await offendingMessage.delete()
                
                pendingSHA256 = result["sha256"]
                self.databaseManager.add(pendingSHA256, np.array(result["embedding"], dtype=np.float32))
                    
                logger.info(f"{user.name} has banned an image. sha256: {pendingSHA256}")
            else:
                msg = "Ran into an error whilst trying to delete the message."
                logger.error("Ran into enternal error trying to delete offending message...")

            deleteResult = self.pendingDatabaseManager.deleteEntry("checks", reactMessageID)
            result = None

            if not deleteResult["before"] > deleteResult["after"]:
                msg = "The pending database has failed to delete the entry."
                logger.error("The database size comparison hasn't changed possible failure of deleting the pending task.")

            await interaction.response.send_message(msg)

        self.stop()


class ConfirmView(discord.ui.View):

    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confrimCallback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"You clicked the button! {self.testData}", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancelCallback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"You clicked the button! {self.testData}", ephemeral=True)
        self.stop()