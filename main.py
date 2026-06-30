import discord
import hashlib
import imagehash
import random
import logging
import torch
import open_clip
import faiss
import numpy as np
import aiohttp
import io
import os
import asyncio
import signal

from pathlib import Path
from PIL import Image
from io import BytesIO
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta, UTC
from collections import deque

from utils import *
from fingerprintDataManager import *
from pendingDataManager import *
from performanceManger import *

if __name__ != "__main__":
    quit()

global logger, resLHits, hateTimer

#Utils funcs.
MSG_LEN_LIMIT = 2000
EMBED_LEN_LIMIT = 4095
SHA256_CHAR_LEN = 64
SCAN_BATCH_SIZE = 30
IMG_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif", ".heic", ".heif", ".avif", ".jfif",] 
# Few formats aren't included due to not working with current set up nor scope.

CONFIG_PATH = "config.json"

def calcImageHash(imageBytes: bytes):
    return (calcSHA256(imageBytes), calcEmbedding(imageBytes))

def calcSHA256(imageBytes: bytes):
    return hashlib.sha256(imageBytes).hexdigest()

def calcEmbedding(imageBytes: bytes):
    return getEmbedding(imageBytes)

def loadImageFolder(folderPath, configDict):
    for filename in os.listdir(folderPath):
        filePath = os.path.join(folderPath, filename)
        if not os.path.isfile(filePath):
            continue

        correctFormat = False
        for ext in IMG_EXTENSIONS:
            if filename.endswith(ext):
                correctFormat = True
                break

        if not correctFormat:
            continue

        try:
            imageData = None
            with open(filePath, "rb") as f:
                imageData = f.read()

            sha, emb = calcImageHash(imageData)
            if databaseManager.add(sha, emb):
                logger.info(f"Image added to database: {filename}")

                if not configDict["Debug"]:#To prevent images being deleted and lost while in development.
                    os.remove(filePath)
                    logger.warning(f"Image deleted {filePath}")
            else:
                logger.warning(f"Failed to add {filename} to the database...")
        except Exception as e:
            logger.error(f"Failed to process image: {filename} | {e}")

def fetchLogs():
    result = ""
    for record in logBuffer:
        result += (f"{record.getMessage()}\n") #TODO think of away to display the further to last message up. As it shows oldest to latest however get cut off.
    return result

#Config const's and load.
DEFAULT_CONFIG = {
    "ServerID" : "",
    "ChannelID" : "",
    "Token" : "",
    "Embedding_Threshold" : 0.87,
    "Debug" : True,
    "CLIP_Processor" : "auto",
    "Jokes_Memes" : False, # Adding this so if someone does use this they can disable my joke out of the bot. 
    "Required_Role_ID" : "", #role id. Replace this with one for your server.
}
configDict = {}
configDict = readJson(CONFIG_PATH, DEFAULT_CONFIG)
writeJson(CONFIG_PATH, configDict)

# Processing queue for scans
scanQueues = {}
resultQueues = {}

#statistics
hitTable = {
    "Img_Scans" : 0,
    "Img_Bans" : 0,
}

#Resenfor Hate :angy: :fist:
RESENFOR_ID = 332634195941654529
MAXIMUM_HITS = 30 # So im not constantly oblitarating him.
hateTimer = datetime.now(UTC)
resLHits = 0

if configDict["Jokes_Memes"]:
    hitTable["L_Res"] = 0
    hitTable["L_Halt"] = True

hitTable = readJson("hits.json", hitTable)

#Perf
perfManager = PerformanceManager()

#Logging
logBuffer = deque(maxlen=500)

class MemoryHandler(logging.Handler):
    def emit(self, record):
        logBuffer.append(record)

logger = logging.getLogger("ClankerMod")#TODO look into which lib either FAISS CLIP or torch adding another logger and disable it.
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)

Path("logs").parent.mkdir(parents=True, exist_ok=True)
timeDateNow = datetime.now(UTC).strftime("%Y-%m-%d")
fileHandler = logging.FileHandler(f"logs/{timeDateNow}-clankerModLog.log", encoding="utf-8")
fileHandler.setFormatter(formatter)

memoryHandler = MemoryHandler()

logger.addHandler(fileHandler)
logger.addHandler(consoleHandler)
logger.addHandler(memoryHandler)

logCleanup("logs")

#CLIP
#CPU Mode or GPU but fall back to CPU if GPU not available.
match(configDict["CLIP_Processor"]):
    case "cpu":
        device = "cpu"
    case _:
        device = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"CLIP + FAISS device: {device}")

model, preprocess, _ = open_clip.create_model_and_transforms(
    "ViT-B-32",
    pretrained="openai"
)
model = model.to(device)
model.eval()

dim = 512
index = faiss.IndexFlatIP(dim)
imageStore = []

@torch.no_grad()
def getEmbedding(imageBytes):
    image = Image.open(io.BytesIO(imageBytes)).convert("RGB")
    image = preprocess(image).unsqueeze(0).to(device)
    emb = model.encode_image(image)
    emb = emb / emb.norm(dim=-1, keepdim=True)
    return emb.cpu().numpy().astype("float32")[0]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
intents.messages = True 

client = commands.Bot(command_prefix = "!" ,intents=intents)

#Banned image load and hash.
databaseManager = FingerprintDataManager()
loadImageFolder("images", configDict)

pendingDatabaseManager = PendingDataManager()

#General Const's
SERVER_ID = configDict["ServerID"]
CHANNEL_ID = configDict["ChannelID"]

@client.event
async def on_ready():
    await registerCommands()

    logger.info(f'Logged in as {client.user}')
    if not updateLoop.is_running():
        updateLoop.start()


async def registerCommands():
    commandFiles = getFiles("commands", "py")
    for file in commandFiles:
        with open(file, "r") as f:
            code = f.read()
            exec(code)
            logger.info(f"Command loaded: {file}")

    guild = discord.Object(id=SERVER_ID)
    client.tree.copy_global_to(guild=guild)
    await client.tree.sync(guild=guild)

async def sendMessage(serverID, channelID, message):
    guild = client.get_guild(serverID)
    if not guild:
        guild = await client.fetch_guild(serverID)

    channel = guild.get_channel(channelID)
    if not channel:
        channel = await client.fetch_channel(channelID)

    msg = await channel.send(message)
    return msg.id

async def getMember(userID):
    guild = client.get_guild(SERVER_ID)
    if guild is None:
        guild = await client.fetch_guild(SERVER_ID)

    member = guild.get_member(userID)
    if member is None:
        member = await guild.fetch_member(userID)

    return member

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

async def getMessage(channelID, messageID):
    guild = client.get_guild(SERVER_ID)
    if guild is None:
        guild = await client.fetch_guild(SERVER_ID)

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
    
async def isInteractionAuthorised(interaction: discord.Interaction):
    if not str(interaction.guild.id) == SERVER_ID:
        await interaction.response.send_message("This is not the guild i serve.", ephemeral=True)
        logger.warning(f"Attempted admin command called by: {interaction.user.name} no actions where performed.")
        return False

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You're not an administrator.", ephemeral=True)
        logger.warning(f"Attempted admin command called by: {interaction.user.name} no actions where performed.")
        return False

    return True

@client.event
async def on_message(message):
    global resLHits, hateTimer
    if message.author == client.user:
        return

    if configDict["Jokes_Memes"]:
        if resLHits < MAXIMUM_HITS and hitTable["L_Halt"]:
            if message.author.id == RESENFOR_ID:
                await message.add_reaction("\U0001F1F1") # Regional L emoji.
                resLHits += 1
                hitTable["L_Res"] += 1
                if resLHits >= MAXIMUM_HITS:
                    hateTimer = datetime.now(UTC)
        
        if datetime.now(UTC) - hateTimer >= timedelta(days=1):
            resLHits = 0
            #hitTable["L_Halt"] = True ## Hehehe. So boring.
    
    for attachment in message.attachments:
        hitTable["Img_Scans"] += 1
        perfManager.begin("IMG SCAN")
        if attachment.content_type and attachment.content_type.startswith("image/"):
            imageBytes = await attachment.read()
            
            imageSHA256 = calcSHA256(imageBytes)
            dbFetchSHA = databaseManager.get(imageSHA256)

            foundMatch = False
            logger.info(f"Image posted: {message.channel} | sha256: {imageSHA256}")
            if dbFetchSHA != None and dbFetchSHA["sha256"] == imageSHA256:
                logger.info(f"Image matching with banned list of sha256: {imageSHA256}")

                timeoutResult = await timeoutUser(message.author)

                msg = f"""
                Image matching in banned list was posted in {message.channel.name} by {message.author.name} 
                \n\nsha256: {imageSHA256}
                \nTimeout success: {timeoutResult} 
                \nReact with :thumbsup: to ban the user.
                """
                msgID = await sendMessage(SERVER_ID, CHANNEL_ID, msg)
                await message.delete()

                pendingDatabaseManager.submitPending(Tables.BANS, {
                    "msgID" : msgID,
                    "time" : datetime.now(UTC).isoformat(),
                    "userID" : message.author.id,
                })
                foundMatch = True
                perfManager.end("IMG SCAN")
                break
            else:
                logger.info(f"Embedding search into database...")
                imageEmb = calcEmbedding(imageBytes)
                dbSearchResult = databaseManager.search(imageEmb, 8)
                
                for resultData in dbSearchResult:
                    embScoreResult = resultData["score"]
                    sha256Result = resultData["sha256"]

                    embeddingMatch =  embScoreResult >= configDict["EmbeddingThreshold"]
                    if embeddingMatch:
                        logger.info(f"Embedding search has found a high probability match with score: {embScoreResult}\nsha256:{sha256Result}")
                        timeoutResult = await timeoutUser(message.author)

                        msg = f"""
                        Image matching in banned list was posted in {message.channel.name} by {message.author.name} 
                        \nEmbedding Score: {embScoreResult}
                        \nTimeout success: {timeoutResult} 
                        \nReact with :thumbsup: to ban the user.
                        """
                        msgID = await sendMessage(SERVER_ID, CHANNEL_ID, msg)
                        await message.delete()

                        pendingDatabaseManager.submitPending(Tables.BANS, {
                            "msgID" : msgID,
                            "time" : datetime.now(UTC).isoformat(),
                            "userID" : message.author.id,
                        })
                        foundMatch = True
                        perfManager.end("IMG SCAN")
                        break

                if foundMatch:
                    break
            
            if not foundMatch:
                logger.info(f"Image has been posted in {message.channel.name} by {message.author.name} sha256: {imageSHA256}")
                msg = f"""
                Image has been posted in {message.channel.name} by {message.author.name} react with :thumbsup: to blacklist. 
                \n[Jump to message](https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id})
                \nsha256: {imageSHA256}
                """ 
                msgID = await sendMessage(SERVER_ID, CHANNEL_ID, msg)

                pendingDatabaseManager.submitPending(Tables.CHECKS, {
                    "msgID" : msgID,
                    "sha256" : imageSHA256,
                    "embedding" : imageEmb,
                    "time" : datetime.now(UTC).isoformat(),
                    "messageID" : message.id,
                    "channelID" : message.channel.id,
                    "userID" : message.author.id,
                })
                perfManager.end("IMG SCAN")

@client.event
async def on_raw_reaction_add(payload):
    user = await getMember(payload.user_id)
    reactMessageID = str(payload.message_id)

    if user.bot:
        return

    if payload.emoji.name == "👍":

        result = pendingDatabaseManager.get(Tables.CHECKS, reactMessageID)
        if result != None:

            if not user.guild_permissions.administrator:
                await sendMessage(SERVER_ID, CHANNEL_ID,"You're not an administrator.")
                logger.warning(f"{user.name} attempted to approve a image ban but aren't administrator.")
                return

            offendingMessage = await getMessage(result["channelID"], result["messageID"])

            msg =  "Added image to banned list."
            if offendingMessage:
                await offendingMessage.delete()
                
                pendingSHA256 = result["sha256"]
                databaseManager.add(pendingSHA256, np.array(result["embedding"], dtype=np.float32))
                    
                logger.info(f"{user.name} has banned an image. sha256: {pendingSHA256}")
            else:
                msg = "Ran into an error whilst trying to delete the message."
                logger.error("Ran into enternal error trying to delete offending message...")

            deleteResult = pendingDatabaseManager.deleteEntry(Tables.CHECKS, reactMessageID)
            result = None

            if deleteResult["before"] - deleteResult["after"] <= 0:
                msg = "The pending database has failed to delete the entry."
                logger.error("The database size comparison hasn't changed possible failure of deleting the pending task.")

            await sendMessage(SERVER_ID, CHANNEL_ID, msg)

        result = pendingDatabaseManager.get(Tables.BANS, reactMessageID)
        if result != None:
            if not user.guild_permissions.administrator:
                await sendMessage(SERVER_ID, CHANNEL_ID, "You're not an administrator.")
                logger.warning(f"{user.name} attempted to approve a ban but aren't administrator.")
                return

            userObj = await getMember(result["userID"])
            banResult = await banUser(userObj)

            await sendMessage(SERVER_ID, CHANNEL_ID, f"The user will be banned. User: {userObj.name} Success: {banResult}") 
            logger.info(f"{user.name} has banned the user {userObj.name}")

            pendingDatabaseManager.deleteEntry(Tables.BANS, reactMessageID)
            
@tasks.loop(seconds=5)
async def scanLoop():
    finished = False
    toDelete = []
    for key in scanQueues.keys():

        msgListSize = len(scanQueues[key])
        if msgListSize <= 0:
            msg =  f"Scan completed. {resultQueues[key]} violating images have been found and deleted."
            logger.info(msg)
            await sendMessage(SERVER_ID, CHANNEL_ID, msg)
            toDelete.append(key)
            finished = True
            break

        for index in range(0, min(SCAN_BATCH_SIZE, msgListSize)):
            message = scanQueues[key].pop()
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith("image/"):
                    imageBytes = await attachment.read()
                    
                    imageSHA256 = calcSHA256(imageBytes)
                    dbFetchSHA = databaseManager.get(imageSHA256)

                    if dbFetchSHA != None and dbFetchSHA["sha256"] == imageSHA256:
                        timeoutResult = await timeoutUser(message.author)
                        await message.delete()

                        if not key in resultQueues.keys():
                            resultQueues[key] = 1
                        else:
                            resultQueues[key]+= 1

                        break
                    else:
                        imageEmb = calcEmbedding(imageBytes)
                        dbSearchResult = databaseManager.search(imageEmb, 8)

                        escapeLoop = False
                        for resultData in dbSearchResult:
                            embScoreResult = resultData["score"]
                            sha256Result = resultData["sha256"]

                            embeddingMatch =  embScoreResult >= configDict["EmbeddingThreshold"]
                            if embeddingMatch:
                                await message.delete()
                                escapeLoop = True

                                if not key in resultQueues.keys():
                                    resultQueues[key] = 1
                                else:
                                    resultQueues[key]+= 1
                                break
                        if escapeLoop:
                            break
    
    if len(toDelete) != 0:
        for key in toDelete:
            del resultQueues[key]
            del scanQueues[key]

    if finished:
        logger.info("Scanner loop stopping...")
        scanLoop.stop()

@tasks.loop(seconds=60)
async def updateLoop():
    for table in Tables:
        resultList = pendingDatabaseManager.fetchAll(table)
        if resultList != None and len(resultList) != 0:
            toDelete = []
            for pending in resultList:
                if hasDaysPassed(datetime.fromisoformat(pending["time"]), days=20):
                    toDelete.append(pending["msgID"])
                    continue

            if len(toDelete) != 0:
                for key in toDelete:
                    pendingDatabaseManager.deleteEntry(table, key)

    writeJson("hits.json", hitTable)

class MyView(discord.ui.View):##TODO move to a secondary file create a ban, blacklist and more buttons to move away from react to button confirms.

    def __init__(self, testData):
        super().__init__(timeout=30)
        self.testData = testData

    @discord.ui.button(label="Click me", style=discord.ButtonStyle.primary)
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"You clicked the button! {self.testData}", ephemeral=True)
        self.stop()


try:
    client.run(configDict["Token"])
finally:
    databaseManager.close()
    pendingDatabaseManager.close()
    writeJson("hits.json", hitTable)
