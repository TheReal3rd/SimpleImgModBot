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
import time

from pathlib import Path
from PIL import Image
from io import BytesIO
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta, UTC
from collections import deque

import globals

from utils import *
from fingerprintDataManager import *
from pendingDataManager import *
from performanceManger import *
from actionsViews import *
from discordUtils import *

if __name__ != "__main__":
    quit()

def calcImageHash(imageBytes: bytes):
    return (calcSHA256(imageBytes), calcEmbedding(imageBytes))
globals.calcImageHashFunc = calcImageHash

def calcSHA256(imageBytes: bytes):
    return hashlib.sha256(imageBytes).hexdigest()
globals.calcSHA256Func = calcSHA256

def calcEmbedding(imageBytes: bytes):
    return getEmbedding(imageBytes)
globals.calcEmbeddingFunc = calcEmbedding

def fetchLogs():
    result = ""
    for record in logBuffer:
        result += (f"{record.getMessage()}\n")
    return result

#Config const's and load.

globals.configDict = readJson(globals.CONFIG_PATH, globals.DEFAULT_CONFIG)
writeJson(globals.CONFIG_PATH, globals.configDict)

# Processing queue for scans
scanQueues = {}
resultQueues = {}
purgeQueues = {}

#statistics
hitTable = {
    "Img_Scans" : 0,
    "Img_Bans" : 0,
}

#Resenfor Hate :angy: :fist:
MAXIMUM_HITS = 30 # So im not constantly oblitarating him.
hateTimer = datetime.now(UTC)
resLHits = 0

if globals.configDict["Jokes_Memes"]:
    hitTable["L_Res"] = 0
    hitTable["L_Halt"] = True

hitTable = readJson("hits.json", hitTable)

#Perf
globals.perfManager = PerformanceManager()

#Logging
logBuffer = deque(maxlen=500)

class MemoryHandler(logging.Handler):
    def emit(self, record):
        logBuffer.append(record)

logger = logging.getLogger("ClankerMod")#TODO look into which lib either FAISS CLIP or torch adding another logger and disable it.
globals.logger = logger
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
match(globals.configDict["CLIP_Processor"]):
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
globals.client = client

#Banned image load and hash.
databaseManager = FingerprintDataManager()
globals.databaseManager = databaseManager
loadImageFolder("images")

pendingDatabaseManager = PendingDataManager()
globals.pendingDatabaseManager = pendingDatabaseManager

#General Const's
globals.SERVER_ID = globals.configDict["ServerID"]
globals.CHANNEL_ID = globals.configDict["ChannelID"]

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

    guild = discord.Object(id=globals.SERVER_ID)
    client.tree.copy_global_to(guild=guild)
    await client.tree.sync(guild=guild)

@client.event
async def on_message(message):
    global resLHits, hateTimer
    if message.author == client.user:
        return

    if globals.configDict["Jokes_Memes"]:
        if resLHits < MAXIMUM_HITS and hitTable["L_Halt"]:
            if message.author.id == globals.RESENFOR_ID:
                await message.add_reaction("\U0001F1F1") # Regional L emoji.
                resLHits += 1
                hitTable["L_Res"] += 1
                if resLHits >= MAXIMUM_HITS:
                    hateTimer = datetime.now(UTC)
        
        if datetime.now(UTC) - hateTimer >= timedelta(days=1):
            resLHits = 0
            #hitTable["L_Halt"] = True ## Hehehe. So boring.
    
    authorUsername = message.author.name
    for attachment in message.attachments:
        hitTable["Img_Scans"] += 1
        globals.perfManager.begin("IMG SCAN")
        if attachment.content_type and attachment.content_type.startswith("image/"):
            imageBytes = await attachment.read()
            
            imageSHA256 = calcSHA256(imageBytes)
            dbFetchSHA = databaseManager.get(imageSHA256)

            foundMatch = False
            logger.info(f"Image posted: {message.channel} | sha256: {imageSHA256}")
            if dbFetchSHA != None and dbFetchSHA["sha256"] == imageSHA256:
                logger.info(f"Image matching with banned list of sha256: {imageSHA256}")

                timeoutResult = await timeoutUser(message.author)

                embed = discord.Embed (
                    title = "Banned Image",
                    description = f"Image matching in banned list was posted in {message.channel.name} by {authorUsername}.",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="SHA256",
                    value = f"{imageSHA256}",
                    inline = False
                )
                embed.add_field(
                    name="Timeout Result:",
                    value = f"{timeoutResult}",
                    inline = False
                )
                embed.set_footer(text="React with 👍 to ban the user")

                confirmButtonView = BanUserView(authorUsername)
                msgID = await sendMessage(globals.SERVER_ID, globals.CHANNEL_ID, embed= embed, view= confirmButtonView)
                await message.delete()

                pendingDatabaseManager.submitPending(Tables.BANS, {
                    "msgID" : msgID,
                    "time" : datetime.now(UTC).isoformat(),
                    "userID" : message.author.id,
                })
                foundMatch = True
                globals.perfManager.end("IMG SCAN")
                break
            else:
                logger.info(f"Embedding search into database...")
                imageEmb = calcEmbedding(imageBytes)
                dbSearchResult = databaseManager.search(imageEmb, 8)
                
                for resultData in dbSearchResult:
                    embScoreResult = resultData["score"]
                    sha256Result = resultData["sha256"]

                    embeddingMatch =  embScoreResult >= globals.configDict["EmbeddingThreshold"]
                    if embeddingMatch:
                        logger.info(f"Embedding search has found a high probability match with score: {embScoreResult}\nsha256:{sha256Result}")
                        timeoutResult = await timeoutUser(message.author)

                        embed = discord.Embed (
                            title = "Banned Image",
                            description = f"Image matching in banned list was posted in {message.channel.name} by {authorUsername}.",
                            color=discord.Color.red()
                        )
                        embed.add_field(
                            name="Embedding Score",
                            value = f"{embScoreResult}",
                            inline = False
                        )
                        embed.add_field(
                            name="Timeout Result:",
                            value = f"{timeoutResult}",
                            inline = False
                        )
                        embed.set_footer(text="React with 👍 to ban the user")

                        confirmButtonView = BanUserView(authorUsername)
                        msgID = await sendMessage(globals.SERVER_ID, globals.CHANNEL_ID, embed=embed, view=confirmButtonView)
                        await message.delete()

                        pendingDatabaseManager.submitPending(Tables.BANS, {
                            "msgID" : msgID,
                            "time" : datetime.now(UTC).isoformat(),
                            "userID" : message.author.id,
                        })
                        foundMatch = True
                        globals.perfManager.end("IMG SCAN")
                        break

                if foundMatch:
                    break
            
            if not foundMatch:
                logger.info(f"Image has been posted in {message.channel.name} by {message.author.name} sha256: {imageSHA256}")

                embed = discord.Embed (
                    title = "Image posted",
                    description = f"Image has been posted in {message.channel.name} by {message.author.name}.",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="SHA256",
                    value = f"{imageSHA256}",
                    inline = False
                )
                embed.add_field(
                    name = "Jump",
                    value = f"[Jump to message](https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id})"
                )
                embed.set_footer(text="React with 👍 to blacklist")

                confirmButtonView = BanImageView()
                msgID = await sendMessage(globals.SERVER_ID, globals.CHANNEL_ID, embed= embed, view=confirmButtonView)

                pendingDatabaseManager.submitPending(Tables.CHECKS, {
                    "msgID" : msgID,
                    "sha256" : imageSHA256,
                    "embedding" : imageEmb,
                    "time" : datetime.now(UTC).isoformat(),
                    "messageID" : message.id,
                    "channelID" : message.channel.id,
                    "userID" : message.author.id,
                })
                globals.perfManager.end("IMG SCAN")

@client.event
async def on_raw_reaction_add(payload):
    user = await getMember(globals.SERVER_ID, payload.user_id)
    reactMessageID = str(payload.message_id)

    if user.bot:
        return

    if payload.emoji.name == "👍":

        result = pendingDatabaseManager.get(Tables.CHECKS, reactMessageID)
        if result != None:

            if not user.guild_permissions.administrator:
                await sendMessage(globals.SERVER_ID, globals.CHANNEL_ID,"You're not an administrator.")
                logger.warning(f"{user.name} attempted to approve a image ban but aren't administrator.")
                return

            offendingMessage = await getMessage(globals.SERVER_ID, result["channelID"], result["messageID"])

            pendingSHA256 = result["sha256"]

            msg =  f"Added image to banned list.\nSHA256: {pendingSHA256}"
            if offendingMessage:
                await offendingMessage.delete()
                
                databaseManager.add(pendingSHA256, np.array(result["embedding"], dtype=np.float32))
                    
                logger.info(f"{user.name} has banned an image. sha256: {pendingSHA256}")
            else:
                msg = "Ran into an error whilst trying to delete the message."
                logger.error("Ran into enternal error trying to delete offending message...")

            deleteResult = pendingDatabaseManager.deleteEntry(Tables.CHECKS, reactMessageID)
            result = None

            if not deleteResult["before"] > deleteResult["after"]:
                msg = "The pending database has failed to delete the entry."
                logger.error("The database size comparison hasn't changed possible failure of deleting the pending task.")

            await sendMessage(globals.SERVER_ID, globals.CHANNEL_ID, msg)

            messageObj = await getMessage(globals.SERVER_ID, globals.CHANNEL_ID, reactMessageID)
            if messageObj:
                await messageObj.delete()

        result = pendingDatabaseManager.get(Tables.BANS, reactMessageID)
        if result != None:
            if not user.guild_permissions.administrator:
                await sendMessage(globals.SERVER_ID, globals.CHANNEL_ID, "You're not an administrator.")
                logger.warning(f"{user.name} attempted to approve a ban but aren't administrator.")
                return

            userObj = await getMember(globals.SERVER_ID, result["userID"])
            banResult = await banUser(userObj, user.name)

            await sendMessage(globals.SERVER_ID, globals.CHANNEL_ID, f"The user will be banned. User: {userObj.name} Success: {banResult}") 
            logger.info(f"{user.name} has banned the user {userObj.name}")

            pendingDatabaseManager.deleteEntry(Tables.BANS, reactMessageID)
            
            messageObj = await getMessage(globals.SERVER_ID, globals.CHANNEL_ID, reactMessageID)
            if messageObj:
                await messageObj.delete()
            
@tasks.loop(seconds=5)
async def scanLoop():
    globals.perfManager.begin("Scan Loop")
    finished = False
    toDelete = []
    for key in scanQueues.keys():

        msgListSize = len(scanQueues[key])
        if msgListSize <= 0:
            msg =  f"Scan completed. {resultQueues[key]} violating images have been found and deleted."
            logger.info(msg)
            await sendMessage(globals.SERVER_ID, globals.CHANNEL_ID, msg)
            toDelete.append(key)
            finished = True
            break

        for index in range(0, min(globals.SCAN_BATCH_SIZE, msgListSize)):
            message = scanQueues[key].pop()
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith("image/"):
                    imageBytes = await attachment.read()
                    
                    imageSHA256 = calcSHA256(imageBytes)
                    dbFetchSHA = databaseManager.get(imageSHA256)

                    if dbFetchSHA != None and dbFetchSHA["sha256"] == imageSHA256:
                        timeoutResult = await timeoutUser(message.author)
                        await message.delete()
                        time.sleep(1)

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

                            embeddingMatch =  embScoreResult >= globals.configDict["EmbeddingThreshold"]
                            if embeddingMatch:
                                await message.delete()
                                time.sleep(1)
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
    globals.perfManager.stop("Update Loop")

@tasks.loop(seconds=10)
async def purgeLoop():
    globals.perfManager.begin("Purge Loop")
    finished = False
    toDelete = []
    for key in purgeQueues.keys():
        msgListSize = len(purgeQueues[key])
        if msgListSize <= 0:
            msg =  f"Purge completed. {resultQueues[key]} messages have been deleted."
            logger.info(msg)
            await sendMessage(globals.SERVER_ID, globals.CHANNEL_ID, msg)
            toDelete.append(key)
            finished = True
            break

        for index in range(0, min(globals.SCAN_BATCH_SIZE, msgListSize)):
            message = purgeQueues[key].pop()
            await message.delete()
            time.sleep(1)

            if not key in resultQueues.keys():
                resultQueues[key] = 1
            else:
                resultQueues[key]+= 1

    if len(toDelete) != 0:
        for key in toDelete:
            del resultQueues[key]
            del purgeQueues[key]

    if finished:
        logger.info("Purge loop stopping...")
        purgeLoop.stop()

    globals.perfManager.end("Purge Loop")


@tasks.loop(seconds=60)
async def updateLoop():
    for table in Tables:
        resultList = pendingDatabaseManager.fetchAll(table)
        if resultList != None and len(resultList) != 0:
            toDelete = []
            for pending in resultList:
                if hasDaysPassed(datetime.fromisoformat(pending["time"]), days=20):
                    logger.info(f"Pending has expired: msgID: {pending["msgID"]}")
                    messageObj = await getMessage(globals.SERVER_ID, globals.CHANNEL_ID, pending["msgID"])
                    if messageObj or messageObj != None:# Not exactly sure what the return would be if the message was already deleted... In the event of missing obj.
                        messageObj.delete()

                    toDelete.append(pending["msgID"])
                    continue

            if len(toDelete) != 0:
                for key in toDelete:
                    pendingDatabaseManager.deleteEntry(table, key)

    writeJson("hits.json", hitTable)

try:
    client.run(globals.configDict["Token"])
finally:
    databaseManager.close()
    pendingDatabaseManager.close()
    writeJson("hits.json", hitTable)
