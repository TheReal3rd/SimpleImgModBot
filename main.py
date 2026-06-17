import discord
import hashlib
import imagehash
import json
import os

from pathlib import Path
from PIL import Image
from io import BytesIO
from discord.ext import commands, tasks
from datetime import datetime, timedelta

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

def loadImageFolder(folderPath, bannedDict):
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

            #os.remove(filePath)
            print(f"Image Folder deleted {filePath}")
        except Exception as e:
            print(f"Failed to process image: {filename} | {e}")

def hasDaysPassed(startTime, days=1):
    return datetime.utcnow() >= startTime + timedelta(days=days)

#Vars

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
intents.messages = True 

client = discord.Client(intents=intents)

#Banned image load and hash.
bannedImageDict = {}
bannedImageDict = readJson("bannedList.json", {})
loadImageFolder("images", bannedImageDict)
writeJson("bannedList.json", bannedImageDict)

#Config const's and load.
DEFAULT_CONFIG = {
    "ServerID" : "",
    "ChannelID" : "",
    "Token" : "",
    "Phash_Threshold" : 5
}
# Phash_Threshold
#0 = identical perceptually
#1-5 = usually same image with compression/resizing
#5-15 = possibly same image with edits
#>15 = likely different images

configDict = {}
configDict = readJson("config.json", DEFAULT_CONFIG)
writeJson("config.json", configDict)

# working
pendingChecksDict = {}

#General Const's
SERVER_ID = configDict["ServerID"]
CHANNEL_ID = configDict["ChannelID"]

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
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
            reason = "ClankerMod - Spam / scam images or banned images posting."
        )
        print(f"User as been timedout for 28 days. User: {user.name}")

    except discord.Forbidden:
        print("Missing required permissions.")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('$hello'):
        await message.channel.send(f"Hello! {message.author.name}")
        return

    for attachment in message.attachments:
        if attachment.content_type and attachment.content_type.startswith("image/"):
            imageBytes = await attachment.read()
            
            imageSHA256, imagePerceptual = calcImageHash(imageBytes)

            print(f"Image posted: {message.channel} | SHA256: {imageSHA256} | Perceptual: {imagePerceptual}")
            if len(bannedImageDict.keys()) != 0:
                for bannedImage in bannedImageDict.keys():
                    dataDict = bannedImageDict[bannedImage]
                    hash256 = bannedImage
                    perceptual = imagehash.hex_to_hash(dataDict["phash"])

                    matching256 = hash256 == imageSHA256
                    perceptualDist = imagehash.hex_to_hash(imagePerceptual) - perceptual <= configDict["Phash_Threshold"]

                    if matching256 or perceptualDist:
                        print(f"Image matching with banned list of SHA256: {imageSHA256} Perceptual: {imagePerceptual}")

                        msg = f"""
                        Image matching in banned list was posted in {message.channel.name} by {message.author.name} 
                        \n\nSHA256: {imageSHA256}\nPerceptual: {imagePerceptual}
                        """
                        await sendMessage(SERVER_ID, CHANNEL_ID, msg)

                        await message.delete()
                        await timeoutUser(message.author)
                        return
            
            msg = f"""
            Image has been posted in {message.channel.name} by {message.author.name} react with :thumbsup: to blacklist. 
            \n[Jump to message](https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id})
            \nSHA256: {imageSHA256}\nPerceptual: {imagePerceptual}
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
        if reaction.message.id == pending:
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