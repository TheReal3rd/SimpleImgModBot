import discord
import asyncio

from time import sleep
from random import randint, choice
from hashlib import sha256
from pathlib import Path
from io import BytesIO
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta, UTC
from PIL import Image

from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.helper import first
from twitchAPI.object.eventsub import StreamOnlineEvent

import globals

from managers.fingerprintDataManager import FingerprintDataManager
from managers.pendingDataManager import PendingDataManager, Tables
from managers.performanceManger import PerformanceManager
from managers.imageManager import ImageManager

from utils.utils import *
from utils.discordUtils import *
from utils.loggingUtils import *
from utils.clipEmbedUtils import initClip, getEmbedding

from actionsViews import *

if __name__ != "__main__":
    quit()

def calcImageHash(imageBytes: bytes):
    return (calcSHA256(imageBytes), calcEmbedding(imageBytes))
globals.calcImageHashFunc = calcImageHash

def calcSHA256(imageBytes: bytes):
    return sha256(imageBytes).hexdigest()
globals.calcSHA256Func = calcSHA256

def calcEmbedding(imageBytes: bytes):
    return getEmbedding(imageBytes)
globals.calcEmbeddingFunc = calcEmbedding

#Config const's and load.

globals.configDict = readJson(globals.CONFIG_PATH, globals.DEFAULT_CONFIG)
writeJson(globals.CONFIG_PATH, globals.configDict)

# Processing queue for scans
scanQueues: dict = {}
resultQueues: dict = {}
purgeQueues: dict = {}

#Resenfor Hate :angy: :fist:
hateTimer: datetime = datetime.now(UTC)
resLHits: int = 0

if globals.configDict["JokesMemes"]:
    globals.DEFAULT_HITTABLE["L_Res"] = 0
    globals.DEFAULT_HITTABLE["L_Halt"] = True

globals.hitTable = readJson(globals.HITS_PATH, globals.DEFAULT_HITTABLE)

#Perf
globals.perfManager: PerformanceManager = PerformanceManager()

#Logging
logger: Logger = initLogging()
globals.logger = logger

#CLIP
initClip()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
intents.messages = True 

client: commands.Bot = commands.Bot(command_prefix = "!" ,intents=intents)
globals.client = client

#Banned image load and hash.
databaseManager: FingerprintDataManager = FingerprintDataManager()
globals.databaseManager = databaseManager
loadImageFolder("images")

pendingDatabaseManager: PendingDataManager = PendingDataManager()
globals.pendingDatabaseManager = pendingDatabaseManager

if globals.configDict["SaveImages"]:
    imageManager = ImageManager(globals.IMAGE_PATH)
    globals.imageManager = imageManager

#General Const's
globals.SERVER_ID = globals.configDict["ServerID"]
globals.CHANNEL_ID = globals.configDict["ChannelID"]

async def handle_channel_online(data: StreamOnlineEvent):
    global twitchPostDelay
    if not datetime.now(UTC) >= twitchPostDelay + timedelta(hours=1):
        logger.info("Twitch API : Canceled notify as 1 hour hasn't passed. Anti spam.")
        return

    channel_name = data.event.broadcaster_user_name
    stream_url = f'https://twitch.tv/{data.event.broadcaster_user_login}'

    config = globals.configDict['Twitch'] # TODO update this to use int id's but as its being 
    notifChannel: str = config['NotifChannel']
    notifRoleID: str = config['NotifRoleID']
    emojiNameID: str = config["NotifEmojiNameID"] # Server emojis have :name:id

    message = f'ATTTENTION <@&{notifRoleID}>, {channel_name} is live! Watch the stream here: {stream_url} <{emojiNameID}>'
    logger.info(f"Twitch API : Detected {channel_name} is live...")
    twitchPostDelay = datetime.now(UTC)

    try:
        await sendMessage(globals.SERVER_ID, notifChannel, message)
    except discord.Forbidden:
        logger.error("Twitch API : Failed to send notification due to lacking permissions.")
    except discord.NotFound:
        logger.error("Twitch API : Failed to send message due to the channel not existing or bot mis configured.")
    except discord.HTTPException as err:
        logger.error(f"Twitch API : Unexpected error. {err}")

def isTwitchConfigValid():
    for key, data in globals.configDict["Twitch"].items():
        if data.trim() == "":
            return False
    return True

# Not sure if all of these are needed, but better safe then sorry.
twitchApi: Twitch | None = None
twitchAuth: UserAuthenticationStorageHelper | None = None
twitchEventSub: EventSubWebsocket | None = None
twitchPostDelay = datetime.now(UTC)

@client.event
async def on_ready():
    await registerCommands()

    await client.change_presence(
        status = discord.Status.online if not globals.configDict["Debug"] else discord.Status.idle,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="The Humans."
        )
    )

    logger.info(f'Logged in as {client.user}')
    if not updateLoop.is_running():
        updateLoop.start()

    if globals.configDict["Debug"]:
        #To prevent spam of the warning msg in channels.
        cancelMsg = False
        msg = "Warning the bot is in a testing state. Kick, Ban and more will do nothing."
        history = await getBotMessageHistory(int(globals.CHANNEL_ID), 20)
        for historyMsg in history: 
            if historyMsg.content == msg:
                cancelMsg = True

        if not cancelMsg:
            await sendMessage(globals.SERVER_ID, globals.CHANNEL_ID, msg)
        logger.warning(msg)

    # Setup the Twitch stuff
    global twitchApi
    global twitchAuth
    global twitchEventSub
    if 'Twitch' not in globals.configDict: # Will no longer work due to rework on how config loads. I'll remove in the future.
        logger.warning("No Twitch configuration found. Continuing without Twitch integration")
        return
    config = globals.configDict['Twitch']

    if not config["Enabled"]:
        logger.info("Twitch Notify has been disabled in configuration. (Tokens Could Expire...)")
        return

    appId = config['AppId']
    appSecret = config['AppSecret']
    channel = config['TwitchChannel']
    oauthCache = Path(config['TokenCache'])

    if appId == "" or appSecret == "" or channel == "" or oauthCache == "":
        logger.warning("No Twitch configuration found. Continuing without Twitch integration")
        return

    twitchApi = await Twitch(appId, appSecret)
    twitchAuth = UserAuthenticationStorageHelper(twitchApi, [], storage_path=oauthCache)
    await twitchAuth.bind()  # This should fetch the tokens from disk and verify them.

    # Make sure the event sub callbacks are executed in this loop
    twitchEventSub = EventSubWebsocket(twitchApi, callback_loop=asyncio.get_running_loop())
    twitchEventSub.start()

    user = await first(twitchApi.get_users(logins=[channel]))
    if user is None:
        raise RuntimeError("Could not locate Twitch Channel!")

    await twitchEventSub.listen_stream_online(user.id, handle_channel_online)

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

async def updateLowResL(message):
    global resLHits, hateTimer
    if globals.configDict["JokesMemes"]:
        if resLHits < globals.MAXIMUM_L and globals.hitTable["L_Halt"]:
            if message.author.id == globals.RESENFOR_ID:
                await message.add_reaction(globals.REGIONAL_L)
                resLHits += 1
                globals.hitTable["L_Res"] += 1
                if resLHits >= globals.MAXIMUM_L:
                    hateTimer = datetime.now(UTC)
        
        if hasDaysPassed(hateTimer):
            resLHits = 0
            #globals.hitTable["L_Halt"] = True ## Hehehe. So boring.

async def handleBannedImage(message: discord.Message, shaEmbedScore):
    timeoutResult = await timeoutUser(message.author)

    embed = buildImageEmbed(message, globals.EmbedPostType.IMG_BAN_SHA, timeoutResult = timeoutResult, shaEmbedScore = str(shaEmbedScore))

    confirmButtonView = BanUserView(message.author.name)
    msgID = await sendMessage(globals.SERVER_ID, globals.CHANNEL_ID, embed= embed, view= confirmButtonView)
    await message.delete()

    pendingDatabaseManager.submitPending(Tables.BANS, {
        "msgID" : msgID,
        "time" : datetime.now(UTC).isoformat(),
        "userID" : message.author.id,
    })

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    await updateLowResL(message)
    
    authorUsername = message.author.name

    for attachment in message.attachments:
        globals.hitTable["Img_Scans"] += 1
        globals.perfManager.begin("Image Scan")
        if attachment.content_type and attachment.content_type.startswith("image/"):
            imageBytes = await attachment.read()
            
            imageSHA256 = calcSHA256(imageBytes)
            dbFetchSHA = databaseManager.get(imageSHA256)

            foundMatch = False
            logger.info(f"Image posted: {message.channel} | sha256: {imageSHA256}")
            if dbFetchSHA != None and dbFetchSHA["sha256"] == imageSHA256:
                logger.info(f"Image matching with banned list of sha256: {imageSHA256}")

                await handleBannedImage(message, imageSHA256)

                if globals.configDict["SaveImages"] and imageManager.getSaveLevel() >= globals.ImageSaveModes.SHA:
                    imageManager.saveImage(imageBytes)

                foundMatch = True
                globals.perfManager.end("Image Scan")
                break
            else:
                logger.info(f"Embedding search into database...")
                imageEmb = calcEmbedding(imageBytes)
                dbSearchResult = databaseManager.search(imageEmb, 8)
                
                for resultData in dbSearchResult:
                    embScoreResult = resultData["score"]
                    sha256Result = resultData["sha256"]

                    embeddingMatch =  embScoreResult >= globals.configDict["EmbeddingThreshold"]
                    if not embeddingMatch:
                        continue

                    logger.info(f"Embedding search has found a high probability match with score: {embScoreResult}\nsha256:{sha256Result}")
                    timeoutResult = await timeoutUser(message.author)

                    await handleBannedImage(message, embScoreResult)

                    if globals.configDict["SaveImages"] and imageManager.getSaveLevel() >= globals.ImageSaveModes.EMBBED:
                        imageManager.saveImage(imageBytes, imageSHA256=imageSHA256, imageEmbedd=imageEmb)

                    foundMatch = True
                    globals.perfManager.end("Image Scan")
                    break

                if foundMatch:
                    break
            
            # Handling the notify of none finger printed images. So not currently banned images.
            if not foundMatch:
                logger.info(f"Image has been posted in {message.channel.name} by {authorUsername} sha256: {imageSHA256}")

                embed = buildImageEmbed(message, globals.EmbedPostType.IMG_POST, shaEmbedScore = str(imageSHA256))

                confirmButtonView = BanImageView()
                msgID = await sendMessage(globals.SERVER_ID, globals.CHANNEL_ID, embed = embed, view = confirmButtonView)

                pendingDatabaseManager.submitPending(Tables.CHECKS, {
                    "msgID" : msgID,
                    "sha256" : imageSHA256,
                    "embedding" : imageEmb,
                    "time" : datetime.now(UTC).isoformat(),
                    "messageID" : message.id,
                    "channelID" : message.channel.id,
                    "userID" : message.author.id,
                })
                if globals.configDict["SaveImages"]:
                    imageManager.saveImage(imageBytes, imageSHA256=imageSHA256)

                globals.perfManager.end("Image Scan")

#Combined the functionality into actionView.py This is now the main section.
@client.event
async def on_raw_reaction_add(payload):
    user = await getMember(globals.SERVER_ID, payload.user_id)
    reactMessageID = str(payload.message_id)

    if user.bot:
        return

    if payload.emoji.name != globals.THUMB_UP:
        return

    if pendingDatabaseManager.exists(Tables.CHECKS, reactMessageID): # React image ban.

        view = ConfirmView(reactMessageID, globals.PendingType.IMAGE_BAN)
        await sendMessage(globals.SERVER_ID, globals.CHANNEL_ID, f"Confirm this image ban:", view=view) 
    
    else: # User ban react.
        if pendingDatabaseManager.exists(Tables.BANS, reactMessageID):

            view = ConfirmView(reactMessageID, globals.PendingType.USER_BAN)
            await sendMessage(globals.SERVER_ID, globals.CHANNEL_ID, f"Confirm this user ban:", view=view) 


async def processAttachments(message, deletions: bool = True, moderation: bool = False):
    resultDict = {
        "violating" : False,
        "timeOutResult": False,
    } 

    for attachment in message.attachments:
        if attachment.content_type and attachment.content_type.startswith("image/"):
            imageBytes = await attachment.read()
                    
            imageSHA256 = calcSHA256(imageBytes)
            dbFetchSHA = databaseManager.get(imageSHA256)

            if dbFetchSHA != None and dbFetchSHA["sha256"] == imageSHA256:
                if moderation:
                    resultDict["timeOutResult"] = await timeoutUser(message.author)

                if deletions:
                    await message.delete()
                resultDict["violating"] = True
                return resultDict
            else:
                imageEmb = calcEmbedding(imageBytes)
                dbSearchResult = databaseManager.search(imageEmb, 8)

                escapeLoop = False
                for resultData in dbSearchResult:
                    embScoreResult = resultData["score"]
                    sha256Result = resultData["sha256"]

                    embeddingMatch =  embScoreResult >= globals.configDict["EmbeddingThreshold"]
                    if embeddingMatch:
                        if moderation:
                            resultDict["timeOutResult"] = await timeoutUser(message.author)

                        if deletions:
                            await message.delete()
              
                        resultDict["violating"] = True
                        return resultDict

    return resultDict

@tasks.loop(seconds=5)
async def scanLoop(): # Manual scan command - commands.scanCommand
    global resultQueues
    globals.perfManager.begin("Scan Loop")
    finished = False
    toDelete = []

    for key in scanQueues.keys():

        if not key in resultQueues.keys():
            resultQueues[key] = 0

        msgListSize = len(scanQueues[key])
        if msgListSize <= 0:
            msg =  f"Scan completed. {resultQueues[key]} violating images has been found and deleted."
            logger.info(msg)
            await sendMessage(globals.SERVER_ID, globals.CHANNEL_ID, msg)
            toDelete.append(key)
            finished = True
            break

        for index in range(0, min(globals.SCAN_BATCH_SIZE, msgListSize)):
            message = scanQueues[key].pop()
            resultDict = await processAttachments(message, True, True)
            if resultDict["violating"]:
                resultQueues[key]+= 1
            sleep(1)

    if len(toDelete) != 0:
        for key in toDelete:
            del resultQueues[key]
            del scanQueues[key]

    if finished:
        logger.info("Scanner loop stopping...")
        scanLoop.stop()
    globals.perfManager.end("Update Loop")

@tasks.loop(seconds=10)
async def purgeLoop(): # purge loop - commands.purgemsgCommand
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
            sleep(1)
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
async def updateLoop(): # Auto saving and auto cleanup cycles.
    global loggerTimer, logger, pendingDatabaseManager
    await pendingDatabaseManager.cleanup()
    if globals.configDict["SaveImages"]:
        imageManager.cleanup()

    writeJson(globals.HITS_PATH, globals.hitTable)

try:
    client.run(globals.configDict["Token"])
finally:
    databaseManager.close()
    pendingDatabaseManager.close()
    writeJson(globals.HITS_PATH, globals.hitTable)
