
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

import globals

logger = logging.getLogger("ClankerMod")

class BanUserView(discord.ui.View):

    def __init__(self, authorUsername):
        super().__init__()
        self.authorUsername = authorUsername

    @discord.ui.button(label="Ban User", style=discord.ButtonStyle.danger)
    async def buttonCallback(self, interaction: discord.Interaction, button: discord.ui.Button):
        confView = ConfirmView(interaction.message.id, globals.PendingType.USER_BAN)
        await interaction.response.send_message(f"Confirm you wish to ban this user: {self.authorUsername}.", view = confView)
        self.stop()


class BanImageView(discord.ui.View):

    @discord.ui.button(label="Ban Image", style=discord.ButtonStyle.danger)
    async def buttonCallback(self, interaction: discord.Interaction, button: discord.ui.Button):
        confView = ConfirmView(interaction.message.id, globals.PendingType.IMAGE_BAN)
        await interaction.response.send_message("Confirm you wish to ban this image.", view = confView)
        self.stop()


class ConfirmView(discord.ui.View):

    def __init__(self, msgID, pendingType: globals.PendingType):
        super().__init__()
        self.msgID = msgID
        self.pendingType = pendingType

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirmCallback(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        reactMessageID = self.msgID
        
        match(self.pendingType): 
            case globals.PendingType.IMAGE_BAN: # IMAGE BANS
                result = globals.pendingDatabaseManager.get("checks", reactMessageID)
                if result != None:

                    if not user.guild_permissions.administrator:
                        await interaction.response.send_message("You're not an Administrator.")
                        logger.warning(f"{user.name} attempted to approve a image ban but aren't Administrator.")
                        return

                    offendingMessage = await getMessage(globals.SERVER_ID, result["channelID"], result["messageID"])
                    pendingSHA256 = result["sha256"]

                    msg =  f"Added image to banned list.\nSHA256: {pendingSHA256}" # TODO later add extra info to allow mods to find the and undo any mistakes.
                    if offendingMessage:
                        await offendingMessage.delete()
                        
                        globals.databaseManager.add(pendingSHA256, np.array(result["embedding"], dtype=np.float32))
                            
                        logger.info(f"{user.name} has banned an image. sha256: {pendingSHA256}")
                    else:
                        msg = "Ran into an error whilst trying to delete the message."
                        logger.error("Ran into enternal error trying to delete offending message...")

                    deleteResult = globals.pendingDatabaseManager.deleteEntry("checks", reactMessageID)
                    result = None

                    if not deleteResult["before"] > deleteResult["after"]:
                        msg = "The pending database has failed to delete the entry."
                        logger.error("The database size comparison hasn't changed possible failure of deleting the pending task.")

                    await interaction.response.send_message(msg)
                    
                    await interaction.message.delete()

            case globals.PendingType.USER_BAN: # USER BANS
                result = globals.pendingDatabaseManager.get("bans", reactMessageID)
                if result != None:
                    if not user.guild_permissions.administrator:
                        await interaction.response.send_message( "You're not an administrator.")
                        logger.warning(f"{user.name} attempted to approve a ban but aren't administrator.")
                        return

                    userObj = await getMember(globals.SERVER_ID, result["userID"])
                    banResult = await banUser(userObj)

                    await interaction.response.send_message( f"The user will be banned. User: {userObj.name} Success: {banResult}") 
                    logger.info(f"{user.name} has banned the user {userObj.name}")

                    globals.pendingDatabaseManager.deleteEntry("bans", reactMessageID)

                    await interaction.message.delete()

        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancelCallback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"The operation has been cancelled.", ephemeral=True)
        await interaction.message.delete()
        self.stop()
