import logging
import discord

from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta, UTC

logger = logging.getLogger("ClankerMod")

# Auth Checks

async def isInteractionAuthorised(interaction: discord.Interaction, serverID):
    if not str(interaction.guild.id) == serverID:
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

async def banUser(user):
    try:
        await user.ban(reason="ClankerMod - User ban after mod approval.")
        logger.info(f"User has been banned forever. User: {user.name}")
        return True
    except discord.Forbidden:
        logger.error("Missing required permissions to ban user.")
    return False

#Fetching

async def getMember(client, serverID, userID):
    guild = client.get_guild(serverID)
    if guild is None:
        guild = await client.fetch_guild(serverID)

    member = guild.get_member(userID)
    if member is None:
        member = await guild.fetch_member(userID)

    return member

async def sendMessage(client, serverID, channelID, message, view=None):
    guild = client.get_guild(serverID)
    if not guild:
        guild = await client.fetch_guild(serverID)

    channel = guild.get_channel(channelID)
    if not channel:
        channel = await client.fetch_channel(channelID)

    msg = await channel.send(message, view = view)
    return msg.id

async def getMessage(client, serverID, channelID, messageID):
    guild = client.get_guild(serverID)
    if guild is None:
        guild = await client.fetch_guild(serverID)

    channel = guild.get_channel(channelID)
    if channel is None:
        channel = await client.fetch_channel(channelID)

    message = await channel.fetch_message(messageID)
    return message

async def getHistory(channel, range):
    messages = []
    async for message in channel.history(limit=range):
        if len(message.attachments) != 0:
            messages.append(message)
    return messages

