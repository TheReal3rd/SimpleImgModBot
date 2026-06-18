import discord
import hashlib
import imagehash
import json
import os
import random
import logging

from pathlib import Path
from PIL import Image
from io import BytesIO
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from collections import deque

if __name__ != "__main__":
    quit()

#Utils funcs.

def readJson(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}

def writeJson(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def calcImageHash(imageBytes: bytes):
    sha = hashlib.sha256(imageBytes).hexdigest()
    img = Image.open(BytesIO(imageBytes))
    phash = str(imagehash.phash(img))
    return (sha, phash)

def loadImageFolder(folderPath, bannedDict):#TODO possible filter none image files from being processed.
    for filename in os.listdir(folderPath):
        filePath = os.path.join(folderPath, filename)

        if not os.path.isfile(filePath):
            continue

        try:
            imageData = None
            with open(filePath, "rb") as f:
                imageData = f.read()

            sha, phash = calcImageHash(imageData)

            bannedDict[sha] = {
                "phash" : phash
            }

            if not configDict["Debug"]:#To prevent images being deleted and lost while in development.
                os.remove(filePath)
                logger.warning(f"Image deleted {filePath}")
        except Exception as e:
            logger.error(f"Failed to process image: {filename} | {e}")

def getFiles(folderPath, endWithFilter):
    result = []
    for filename in os.listdir(folderPath):
        filePath = os.path.join(folderPath, filename)

        if not os.path.isfile(filePath):
            continue
             
        if not filePath.endswith(endWithFilter):
            continue
   
        result.append(filePath)

    return result

def hasDaysPassed(startTime, days=1):
    return datetime.utcnow() >= startTime + timedelta(days=days)

def fetchLogs():
    result = []
    for record in logBuffer:
        result.append(f"{record.created} | {record.getMessage()}")
    return result

#Logging
logBuffer = deque(maxlen=500)

class MemoryHandler(logging.Handler):
    def emit(self, record):
        logBuffer.append(record)

logger = logging.getLogger("ClankerMod")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)

fileHandler = logging.FileHandler("bot.log", encoding="utf-8")
fileHandler.setFormatter(formatter)

memoryHandler = MemoryHandler()

logger.addHandler(fileHandler)
logger.addHandler(consoleHandler)
logger.addHandler(memoryHandler)

#Vars

#Config const's and load.
DEFAULT_CONFIG = {
    "ServerID" : "",
    "ChannelID" : "",
    "Token" : "",
    "Phash_Threshold" : 5,
    "Debug" : True,
}
# Phash_Threshold
#0 = identical perceptually
#1-5 = usually same image with compression/resizing
#5-15 = possibly same image with edits
#>15 = likely different images

configDict = {}
configDict = readJson("config.json", DEFAULT_CONFIG)
writeJson("config.json", configDict)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
intents.messages = True 

client = commands.Bot(command_prefix = "!" ,intents=intents)

#Banned image load and hash.
bannedImageDict = {}
bannedImageDict = readJson("bannedList.json", {})
loadImageFolder("images", bannedImageDict)
writeJson("bannedList.json", bannedImageDict)

# working
pendingChecksDict = {}

#General Const's
SERVER_ID = configDict["ServerID"]
CHANNEL_ID = configDict["ChannelID"]
MSG_LEN_LIMIT = 2000
EMBED_LEN_LIMIT = 4095

@client.event
async def on_ready():
    commandFiles = getFiles("commands", "py")
    for file in commandFiles:
        with open(file, "r") as f:
            code = f.read()
            exec(code)
            logger.info(f"Command loaded: {file}")


    guild = discord.Object(id=SERVER_ID)
    client.tree.copy_global_to(guild=guild)
    await client.tree.sync(guild=guild)

    logger.info(f'Logged in as {client.user}')
    if not update_loop.is_running():
        update_loop.start()

async def sendMessage(serverID, channelID, message):
    guild = client.get_guild(serverID)
    if not guild:
        guild = await client.fetch_guild(serverID)

    channel = guild.get_channel(channelID)
    if not channel:
        channel = await client.fetch_channel(channelID)

    msg = await channel.send(message)
    return msg.id

async def timeoutUser(user):
    try:
        await user.timeout(
            timedelta(days=28),
            reason = "ClankerMod - Spam / Scam images or banned images posting."
        )
        logger.info(f"User as been timedout for 28 days. User: {user.name}")

    except discord.Forbidden:
        logger.error("Missing required permissions.")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    for attachment in message.attachments:
        if attachment.content_type and attachment.content_type.startswith("image/"):
            imageBytes = await attachment.read()
            
            imageSHA256, imagePerceptual = calcImageHash(imageBytes)

            logger.info(f"Image posted: {message.channel} | sha256: {imageSHA256} | phash: {imagePerceptual}")
            if len(bannedImageDict.keys()) != 0:
                for bannedImage in bannedImageDict.keys():
                    dataDict = bannedImageDict[bannedImage]
                    hash256 = bannedImage
                    perceptual = imagehash.hex_to_hash(dataDict["phash"])

                    matching256 = hash256 == imageSHA256
                    perceptualDist = imagehash.hex_to_hash(imagePerceptual) - perceptual <= configDict["Phash_Threshold"]

                    if matching256 or perceptualDist:
                        logger.info(f"Image matching with banned list of sha256: {imageSHA256} phash: {imagePerceptual}")

                        msg = f"""
                        Image matching in banned list was posted in {message.channel.name} by {message.author.name} 
                        \n\nsha256: {imageSHA256}\nphash: {imagePerceptual}
                        """
                        await sendMessage(SERVER_ID, CHANNEL_ID, msg)

                        await message.delete()
                        await timeoutUser(message.author)
                        return
            
            msg = f"""
            Image has been posted in {message.channel.name} by {message.author.name} react with :thumbsup: to blacklist. 
            \n[Jump to message](https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id})
            \nsha256: {imageSHA256}\nphash: {imagePerceptual}
            """ 
            msgID = await sendMessage(SERVER_ID, CHANNEL_ID, msg)

            pendingChecksDict[msgID] = {
                "sha256" : imageSHA256,
                "phash" : perceptual,
                "time" : datetime.utcnow(),
                "messageObj" : message
            }
            return
       
@client.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    toDelete = []
    for key in pendingChecksDict.keys():
        if reaction.message.id == key:
            if reaction.emoji == "👍":
                await reaction.message.channel.send("Added image to banned list!") 

                pendingData = Dict[key]
                await pendingData["messageObj"].delete()
                bannedImageDict[pendingData["sha256"]] = {"phash" : str(pendingData["phash"])}

                toDelete.append(key)
                writeJson("bannedList.json", bannedImageDict)

    if len(toDelete) != 0:
        for key in toDelete:
            del pendingChecksDict[key]


@tasks.loop(seconds=60)
async def update_loop():
    if len(pendingChecksDict.keys()) <= 0:
        return

    toDelete = []
    for key in pendingChecksDict.keys():
        pending = pendingChecksDict[key]

        if hasDaysPassed(pending["time"], days=20):
            toDelete.append(key)
            continue

    if len(toDelete) != 0:
        for key in toDelete:
            del pendingChecksDict[key]



client.run(configDict["Token"])