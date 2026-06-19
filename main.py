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

from pathlib import Path
from PIL import Image
from io import BytesIO
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from collections import deque
from utils import *

if __name__ != "__main__":
    quit()

#Utils funcs.

IMG_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif", ".heic", ".heif", ".avif", ".jfif",] 
# Few formats aren't included due to not working with current set up nor scope.

def calcImageHash(imageBytes: bytes):
    sha = hashlib.sha256(imageBytes).hexdigest()
    img = Image.open(BytesIO(imageBytes))
    phash = str(imagehash.phash(img))
    emb = getEmbedding(imageBytes)
    return (sha, phash, emb)

def loadImageFolder(folderPath, bannedDict, configDict):
    for filename in os.listdir(folderPath):
        correctFormat = False
        for ext in IMG_EXTENSIONS:
            if filename.endswith(ext):
                correctFormat = True
                break

        if not correctFormat:
            continue

        filePath = os.path.join(folderPath, filename)

        if not os.path.isfile(filePath):
            continue

        try:
            imageData = None
            with open(filePath, "rb") as f:
                imageData = f.read()

            sha, phash, emb = calcImageHash(imageData)

            bannedDict[sha] = {
                "phash" : phash,
                "embedding" : emb.tolist()
            }

            if not configDict["Debug"]:#To prevent images being deleted and lost while in development.
                os.remove(filePath)
                logger.warning(f"Image deleted {filePath}")
        except Exception as e:
            logger.error(f"Failed to process image: {filename} | {e}")

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

#CLIP

device = "cuda" if torch.cuda.is_available() else "cpu"

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

def cosineSimilarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

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
loadImageFolder("images", bannedImageDict, configDict)
writeJson("bannedList.json", bannedImageDict)

# working
pendingChecksDict = {}

#General Const's
SERVER_ID = configDict["ServerID"]
CHANNEL_ID = configDict["ChannelID"]
MSG_LEN_LIMIT = 2000
EMBED_LEN_LIMIT = 4095
IMG_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif", ".heic", ".heif", ".avif", ".jfif",] 
# Few formats aren't included due to not working with current set up nor scope.

@client.event
async def on_ready():
    await registerCommands()

    logger.info(f'Logged in as {client.user}')
    if not update_loop.is_running():
        update_loop.start()

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
            
            imageSHA256, imagePerceptual, imageEmb = calcImageHash(imageBytes)

            logger.info(f"Image posted: {message.channel} | sha256: {imageSHA256} | phash: {imagePerceptual}")
            if len(bannedImageDict.keys()) != 0:
                for bannedImage in bannedImageDict.keys():
                    dataDict = bannedImageDict[bannedImage]
                    hash256 = bannedImage
                    perceptual = imagehash.hex_to_hash(dataDict["phash"])
                    emb = dataDict["embedding"]

                    matching256 = hash256 == imageSHA256
                    perceptualDist = imagehash.hex_to_hash(imagePerceptual) - perceptual <= configDict["Phash_Threshold"]
                    embeddingScore = cosineSimilarity(imageEmb, emb)
                    embeddingMatch =  embeddingScore >= 0.87

                    if matching256 or perceptualDist or embeddingMatch:
                        logger.info(f"Image matching with banned list of sha256: {imageSHA256} phash: {imagePerceptual} emb score: {embeddingScore}")

                        msg = f"""
                        Image matching in banned list was posted in {message.channel.name} by {message.author.name} 
                        \n\nsha256: {imageSHA256}\nphash: {imagePerceptual}\nemb: {embeddingScore}
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
                "embedding" : emb.tolist(),
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
                bannedImageDict[pendingData["sha256"]] = {
                    "phash" : str(pendingData["phash"]),
                    "embedding" : pendingData["embedding"]
                }

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