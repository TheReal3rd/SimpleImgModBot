import discord

from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta, UTC
from logging import getLogger

import globals

logger = getLogger("ClankerMod")

# Auth Checks

async def isInteractionAuthorised(interaction: discord.Interaction):
    return await isInterationAdmin(interaction.user) and await isInteractionAuthServer(interaction)

async def isInteractionAuthServer(interaction: discord.Interaction, responseMSG="This is not the guild i serve.", loggerMSG = "no actions where performed."):
    if not str(interaction.guild.id) == globals.SERVER_ID:
        await interaction.response.send_message(responseMSG, ephemeral=True)
        logger.warning(f"Attempted admin command or action called by: {interaction.user.name} {loggerMSG}")
        return False
    return True

async def isInterationAdmin(user, responseMSG="You're not an administrator.", loggerMSG="no actions where performed.", interaction: discord.Interaction = None):
    if not user.guild_permissions.administrator:
        if interaction != None:
            await interaction.response.send_message(responseMSG, ephemeral=True)
        logger.warning(f"Attempted admin command or action called by: {user.name} {loggerMSG}")
        return False
    return True

async def failureMessage(loggerMSG, responseMSG, interaction=None):
    if interaction != None:
        await interaction.response.send_message(responseMSG) 
    else:
        await sendMessage(globals.SERVER_ID, globals.CHANNEL_ID, responseMSG)
    logger.info(f"{loggerMSG}, {responseMSG}")

#Actions

async def timeoutUser(user, days=28):
    if globals.configDict["Debug"]:
        logger.info(f"IN TEST MODE!!! User would have been timedout. User: {user.name}")
        return True

    try:
        await user.timeout(timedelta(days=days), reason = "ClankerMod - Spam / Scam images or banned images posting.")
        logger.info(f"User has been timedout for 28 days. User: {user.name}")
        return True
    except discord.Forbidden:
        logger.error("Missing required permissions to timeout user.")
    return False

async def kickUser(user, authorisedUser=""):
    if globals.configDict["Debug"]:
        logger.info(f"IN TEST MODE!!! User would have been kicked. User: {user.name} Auth by: {authorisedUser}")
        return True

    try:
        await user.kick(reason="ClankerMod - User kick after mod approval.")
        logger.info(f"User has been kicked. User: {user.name} Auth by: {authorisedUser}")
        return True
    except discord.Forbidden:
        logger.error("Missing required permissions to kick user.")
    return False

async def banUser(user, authorisedUser="", applyCounter: bool = True):
    if globals.configDict["Debug"]:
        logger.info(f"IN TEST MODE!!! User would have been banned. User: {user.name} Auth by: {authorisedUser}")
        return True

    try:
        await user.ban(reason="ClankerMod - User ban after mod approval.")
        logger.info(f"User has been banned forever. User: {user.name} Auth by: {authorisedUser}")
        if applyCounter:
            if "BanCount" in globals.hitTable.keys():
                globals.hitTable["BanCount"] += 1
            else:
                globals.hitTable["BanCount"] = 1
        return True
    except discord.Forbidden:
        logger.error("Missing required permissions to ban user.")
    return False

#Fetching

async def getMember(serverID, userID):
    guild = globals.client.get_guild(serverID)
    if guild is None:
        guild = await globals.client.fetch_guild(serverID)

    member = guild.get_member(userID)
    if member is None:
        member = await guild.fetch_member(userID)

    return member

async def sendMessage(serverID, channelID, message="", embed = None, view=None):
    guild = globals.client.get_guild(serverID)
    if not guild:
        guild = await globals.client.fetch_guild(serverID)

    channel = guild.get_channel(channelID)
    if not channel:
        channel = await globals.client.fetch_channel(channelID)

    msg = await channel.send(message, embed = embed, view = view)
    return msg.id

async def getMessage(serverID, channelID, messageID):
    guild = globals.client.get_guild(serverID)
    if guild is None:
        guild = await globals.client.fetch_guild(serverID)

    channel = guild.get_channel(channelID)
    if channel is None:
        channel = await globals.client.fetch_channel(channelID)

    message = await channel.fetch_message(messageID)
    return message

async def getHistoryWithAttachments(channel, range):
    messages = []
    async for message in channel.history(limit=range):
        if len(message.attachments) != 0:
            messages.append(message)
    return messages

async def getBotMessageHistory(channel, range):
    if type(channel) == str:
        guild = globals.client.get_guild(globals.SERVER_ID)
        if guild is None:
            guild = await globals.client.fetch_guild(globals.SERVER_ID)

        channelID = channel

        channel = guild.get_channel(channelID)
        if channel is None:
            channel = await globals.client.fetch_channel(channelID)

    messages = []
    async for message in channel.history(limit=range):
        if message.author.id == globals.client.user.id:
            messages.append(message)
    return messages
