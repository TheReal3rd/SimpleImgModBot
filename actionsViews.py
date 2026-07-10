import discord
import numpy as np

from logging import getLogger
from discord import app_commands
from discord.ext import commands, tasks

from utils.discordUtils import *

import globals

"""
Style	Enum	Appearance	Typical Use
Primary	discord.ButtonStyle.primary	Blue	Main action
Secondary	discord.ButtonStyle.secondary	Gray	Neutral actions
Success	discord.ButtonStyle.success	Green	Confirm/Accept
Danger	discord.ButtonStyle.danger	Red	Delete/Cancel
Link	discord.ButtonStyle.link	Gray (opens URL)	External links
"""

logger = getLogger("ClankerMod")

class BanUserView(discord.ui.View):

    def __init__(self, authorUsername):
        super().__init__()
        self.authorUsername = authorUsername

    @discord.ui.button(label="Ban User", style=discord.ButtonStyle.danger)
    async def buttonCallback(self, interaction: discord.Interaction, button: discord.ui.Button):
        confView = ConfirmView(interaction.message.id, globals.PendingType.USER_BAN)
        await interaction.response.send_message(f"Confirm you wish to ban this user: {self.authorUsername}.", view = confView)

class RequiredRoleUserView(discord.ui.View):

    def __init__(self, badUserDict: dict):
        super().__init__()
        self.args: dict = {}
        self.args["badUserData"] = badUserDict

    @discord.ui.button(label="Kick All Users", style=discord.ButtonStyle.danger)
    async def kickCallback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.args["action"] = "kick"
        confView = ConfirmView(interaction.message.id, globals.PendingType.ROLE_USER_BAN, args = self.args)
        await interaction.response.send_message(f"Confirm you wish to kick all these users.", view = confView)

    @discord.ui.button(label="Ban All Users", style=discord.ButtonStyle.danger)
    async def banCallback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.args["action"] = "ban"
        confView = ConfirmView(interaction.message.id, globals.PendingType.ROLE_USER_BAN, args = self.args)
        await interaction.response.send_message(f"Confirm you wish to ban all these users.", view = confView)

    @discord.ui.button(label="Give All Users Role", style=discord.ButtonStyle.primary)
    async def giveCallback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.args["action"] = "give"
        confView = ConfirmView(interaction.message.id, globals.PendingType.ROLE_USER_BAN, args = self.args)
        await interaction.response.send_message(f"Confirm you wish to give all these users their missing role.", view = confView)

class BanImageView(discord.ui.View):

    @discord.ui.button(label="Ban Image", style=discord.ButtonStyle.danger)
    async def buttonCallback(self, interaction: discord.Interaction, button: discord.ui.Button):
        confView = ConfirmView(interaction.message.id, globals.PendingType.IMAGE_BAN)
        await interaction.response.send_message("Confirm you wish to ban this image.", view = confView)

class ConfirmView(discord.ui.View):

    def __init__(self, msgID, pendingType: globals.PendingType, args={}):
        super().__init__()
        self.msgID = msgID
        self.pendingType = pendingType
        self.args = args

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirmCallback(self, interaction: discord.Interaction, button: discord.ui.Button):
        authorisedUser = interaction.user
        messageID = self.msgID
        serverID = globals.SERVER_ID

        match(self.pendingType): 
            case globals.PendingType.IMAGE_BAN: # IMAGE BANS
                if not await isInterationAdmin(interaction.user, loggerMSG="attempted to approve a image ban but aren't Administrator.", interaction=interaction):
                    return

                result = globals.pendingDatabaseManager.get("checks", messageID)
                if result == None: 
                    await failureMessage(
                        loggerMSG=f"Attempted image ban by {authorisedUser}", 
                        responseMSG="Failed to find the image ban request in pending database.", 
                        interaction=interaction
                    )
                    return

                offendingMessage = await getMessage(serverID, result["channelID"], result["messageID"])
                pendingSHA256 = result["sha256"]

                responseMSG =  f"Added image to banned list.\nSHA256: {pendingSHA256}"
                if offendingMessage:
                    await offendingMessage.delete()
                        
                    globals.databaseManager.add(pendingSHA256, np.array(result["embedding"], dtype=np.float32))
                            
                    logger.info(f"{authorisedUser} has banned an image. sha256: {pendingSHA256}")
                else:
                    responseMSG = "Ran into an error whilst trying to delete the message."
                    logger.error("Ran into enternal error trying to delete offending message...")

                deleteResult = globals.pendingDatabaseManager.deleteEntry("checks", messageID)
                result = None

                if not deleteResult["before"] > deleteResult["after"]:
                    responseMSG = "The pending database has failed to delete the entry."
                    logger.error("The database size comparison hasn't changed possible failure of deleting the pending task.")

                await interaction.response.send_message(responseMSG)
                    
                await interaction.message.delete()

            case globals.PendingType.USER_BAN: # USER BANS
                if not await isInterationAdmin(interaction.user, loggerMSG="attempted to approve a ban but aren't administrator."):
                    return

                result = globals.pendingDatabaseManager.get("bans", messageID)
                if result == None:
                    await failureMessage(
                        loggerMSG=f"Attempted user ban by {authorisedUser}", 
                        responseMSG="Failed to find the ban request in pending database.", 
                        interaction=interaction
                    )
                    return

                userObj = await getMember(serverID, result["userID"])
                banResult = await banUser(userObj, authorisedUser)

                await interaction.response.send_message( f"The user will be banned. User: {userObj.name} Success: {banResult}") 
                logger.info(f"{authorisedUser} has banned the user {userObj.name}")

                globals.pendingDatabaseManager.deleteEntry("bans", messageID)

                await interaction.message.delete()
            
            case globals.PendingType.ROLE_USER_BAN: # Missing Role user bans, kick and give
                keys = self.args.keys()
                if not "badUserData" in keys or not "action" in keys:
                    await failureMessage(
                        loggerMSG=f"Attempted to complete rolescan operation by {authorisedUser}", 
                        responseMSG="Missing required data to proceed with operation argument failed to feed? or Invalid.", 
                        interaction=interaction
                    )
                    return

                action: str = self.args["action"]
                userData: dict = self.args["badUserData"]
                counter: int = 0 # Count how many successes.
                channelID = interaction.channel.id

                role: discord.role = None

                if action == "give":
                    client = globals.client

                    guild: discord.guild = client.get_guild(globals.SERVER_ID)
                    if not guild:
                        guild = await client.fetch_guild(globals.SERVER_ID)

                    if guild:
                        role = guild.get_role(int(globals.configDict["RequiredRoleID"]))

                    if not role:
                        await failureMessage(
                            loggerMSG=f"Attempted to complete rolescan operation by {authorisedUser}.",
                            responseMSG="Failed to fetch the role to be giving to users. Ensure the ID is correct.",
                            interaction=interaction
                        )
                        return

                await interaction.response.send_message("Started...")
                for userID in userData.keys():
                    member: discord.member = await getMember(serverID, userID)
                    if not member:
                        continue

                    result: bool = False
                    
                    match (action):
                        case "kick":
                            result = await kickUser(member, authorisedUser)

                        case "ban":
                            result = await banUser(member, authorisedUser)

                        case "give":
                            if globals.configDict["Debug"]:
                                logger.info(f"IN TEST MODE!!! Would have given {member.name} role {role.name}")
                                continue
                            
                            result = await member.add_role(role)
                            
                    if result:
                        counter += 1

                await sendMessage(serverID, channelID, f"{action} operation has been completed. {counter}/{len(userData.keys())} have been completed.")

        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancelCallback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"The operation has been cancelled.", ephemeral=True)
        await interaction.message.delete()
        self.stop()
