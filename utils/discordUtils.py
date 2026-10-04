from sre_compile import dis
import discord

from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta, UTC
from logging import getLogger

import globals

logger = getLogger("ClankerMod")

# Auth Checks

async def isInteractionAuthorised(interaction: discord.Interaction) -> bool:
    return await isInterationAdmin(interaction.user) and await isInteractionAuthServer(interaction)

async def isInteractionAuthServer(
                                interaction: discord.Interaction, 
                                responseMSG="This is not the guild i serve.", 
                                loggerMSG = "no actions where performed."
                            ) -> bool:
    if not interaction.guild.id == globals.SERVER_ID:
        await interaction.response.send_message(responseMSG, ephemeral=True)
        logger.warning(f"[ServerAuth] Attempted admin command or action called by: {interaction.user.name} {loggerMSG}")
        return False
    return True

async def isInterationAdmin(
                            user: discord.User, 
                            responseMSG="You're not an administrator.", 
                            loggerMSG="no actions where performed.", 
                            interaction: discord.Interaction = None
                        ) -> bool:
    member = await getMember(globals.SERVER_ID, user.id)
    if not member.guild_permissions.administrator:
        if interaction != None:
            await interaction.response.send_message(responseMSG, ephemeral=True)
        logger.warning(f"[AdminAuth] Attempted admin command or action called by: {user.name} {loggerMSG}")
        return False
    return True

async def failureMessage(loggerMSG: str, responseMSG: str, interaction: discord.Interaction=None) -> None:
    if interaction != None:
        await interaction.response.send_message(responseMSG) 
    else:
        await sendMessage(globals.SERVER_ID, globals.CHANNEL_ID, responseMSG)
    logger.info(f"{loggerMSG}, {responseMSG}")

#Actions

async def timeoutUser(user: discord.User, days:int=28) -> bool:
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

async def kickUser(user: discord.User, authorisedUser:str="") -> bool:
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

async def banUser(user: discord.User, authorisedUser:str="", applyCounter: bool = True) -> bool:
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

async def getMember(serverID, userID) -> discord.member:
    guild = globals.client.get_guild(serverID)
    if guild is None:
        guild = await globals.client.fetch_guild(serverID)

    member = guild.get_member(userID)
    if member is None:
        member = await guild.fetch_member(userID)

    return member

async def getChannel(serverID: int, channelID: int) -> discord.channel:
    guild = globals.client.get_guild(serverID)
    if not guild:
        guild = await globals.client.fetch_guild(serverID)

    channel = guild.get_channel(channelID)
    if not channel:
        channel = await globals.client.fetch_channel(channelID)
    return channel

async def sendMessage(serverID: int, channelID: int, message:str="", embed: discord.Embed = None, view: discord.ui.View=None) -> int:
    channel = await getChannel(serverID, channelID)
    msg = await channel.send(message, embed = embed, view = view)
    return msg.id

async def getMessage(serverID: int, channelID: int, messageID: int) -> discord.Message:
    channel = await getChannel(serverID, channelID)
    message = await channel.fetch_message(messageID)
    return message

async def getHistoryWithAttachments(channelID: int, range: int) -> list[discord.Message]:
    channel = await getChannel(globals.SERVER_ID, channelID)
    messages = []
    async for message in channel.history(limit=range):
        if len(message.attachments) != 0:
            messages.append(message)
    return messages

async def getBotMessageHistory(channelID: int, range: int) -> list[discord.Message]:
    channel = await getChannel(globals.SERVER_ID, channelID)
    messages = []
    async for message in channel.history(limit=range):
        if message.author.id == globals.client.user.id:
            messages.append(message)
    return messages

def buildImageEmbed(message, embedType, timeoutResult: bool = False, shaEmbedScore: str = ""):
    authorUsername = message.author.name
    channelName = message.channel.name

    embed = None
    if not embedType == globals.EmbedPostType.IMG_POST:
        embed = discord.Embed (
            title = "Banned Image",
            description = f"Image matching in banned list was posted in {channelName} by {authorUsername}.",
            color=discord.Color.red()
        )
    else:
        embed = discord.Embed (
            title = "Image posted",
            description = f"Image has been posted in {channelName} by {authorUsername}.",
            color=discord.Color.green()
        )

    match embedType:
        case globals.EmbedPostType.IMG_BAN_SHA | globals.EmbedPostType.IMG_POST:
            embed.add_field(
                name="SHA256",
                value = f"{shaEmbedScore}",
                inline = False
            )

        case globals.EmbedPostType.IMG_BAN_EMB:
            embed.add_field(
                name="Embedding Score",
                value = f"{shaEmbedScore}",
                inline = False
            )

    if not embedType == globals.EmbedPostType.IMG_POST:
        embed.add_field(
            name="Timeout Result:",
            value = f"{timeoutResult}",
            inline = False
        )
        embed.set_footer(text="React with 👍 to ban the user")
    else:
        embed.add_field(
            name = "Jump",
            value = f"[Jump to message](https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id})"
        )
        embed.set_footer(text="React with 👍 to blacklist")
    return embed
