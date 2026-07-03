import logging
import discord

from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta, UTC

import globals

logger = logging.getLogger("ClankerMod")

# Auth Checks

async def isInteractionAuthorised(interaction: discord.Interaction):
    if not str(interaction.guild.id) == globals.SERVER_ID:
        await interaction.response.send_message("This is not the guild i serve.", ephemeral=True)
        logger.warning(f"Attempted admin command called by: {interaction.user.name} no actions where performed.")
        return False

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You're not an administrator.", ephemeral=True)
        logger.warning(f"Attempted admin command called by: {interaction.user.name} no actions where performed.")
        return False

    return True

#Actions

async def timeoutUser(user):
    try:
        await user.timeout(timedelta(days=28), reason = "ClankerMod - Spam / Scam images or banned images posting.")
        logger.info(f"User has been timedout for 28 days. User: {user.name}")
        return True
    except discord.Forbidden:
        logger.error("Missing required permissions to timeout user.")
    return False

async def banUser(user, authorisedUser=""):
    try:
        await user.ban(reason="ClankerMod - User ban after mod approval.")
        logger.info(f"User has been banned forever. User: {user.name} Auth by: {authorisedUser}")
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
    messages = []
    async for message in channel.history(limit=range):
        if message.author.id == globals.client.user.id:
            messages.append(message)
    return messages


       

