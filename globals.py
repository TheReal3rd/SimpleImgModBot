from enum import IntEnum, StrEnum
from logging import Logger

from discord.ext import commands
from managers.fingerprintDataManager import FingerprintDataManager
from managers.pendingDataManager import PendingDataManager
from managers.performanceManger import PerformanceManager
from managers.imageManager import ImageManager

class PendingType(StrEnum):
    IMAGE_BAN = "imageBan"
    USER_BAN = "userBan"
    ROLE_USER_BAN = "roleUserBan"

class EmbedPostType(IntEnum):
    IMG_POST = 0
    IMG_BAN_SHA = 1
    IMG_BAN_EMB = 2

#Const
SERVER_ID: int = -1
CHANNEL_ID: int = -1
THUMB_UP: str = "\U0001F44D"

MSG_LEN_LIMIT: int = 2000
EMBED_LEN_LIMIT: int = 4095
SHA256_CHAR_LEN: int = 64
SCAN_BATCH_SIZE: int = 15
IMG_EXTENSIONS: list[str] = [".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif", ".heic", ".heif", ".avif", ".jfif",] 
# Few formats aren't included due to not working with current set up nor scope.

CONFIG_PATH: str = "config.json"
IMAGE_PATH: str = "working_images/"

DEFAULT_CONFIG: dict = {
    "ServerID" : 0,
    "ChannelID" : 0,
    "Token" : "",
    "EmbeddingThreshold" : 0.87,
    "Debug" : False, # Disables Kick, Ban and image deletions for db calls used to test whether the operations reach them.
    "ClipProcessor" : "auto",
    "JokesMemes" : True, # Adding this so if someone does use this they can disable my jokes out of the bot. 
    "RequiredRoleID" : "", #role id. Replace this with one for your server.
    "Twitch": {
        "Enabled" : False, # Force Enablement and Disablement.
        "TwitchChannel": "",  # Twitch channel log-in name of the channel you want live notifications for
        "TokenCache": "", # filepath to a json file containing the OAuth tokens
        "AppId": "",  # Twitch App ID.
        "AppSecret": "",  # Twitch App Secret
        "NotifChannel": "",  # Discord channel ID you want the bot to send the notifications on
        "NotifRole": ""  # Role you want the bot to ping. Do not include the '@'
    },
    "PendingKeepDays" : 20, # The number of days maximum to keep pending bans and checks. 
    "MonthLogsCleanup" : 2, # The Duration for how long logs will be kept. In Months
    "SaveImages" : False, # Allows the bot to save the images. To allow the administrator to review images to add to the block list.
}

ABT_MSG: list[str] = [
    "4d61646520627920337264",
    "Resenfor Smells.",
    "Dargo is a cutie pie! :3",
    "Andromeda show me ur package.",
    "Tin Tin is a cootie. :3",
    "Resenfor is sometimes cute.",
    "E",
    "3.1415926535",
    "Beep Boop...",
]

HITS_PATH: str = "hits.json" # Was only for Resenfor react but used to store other useful data.
DEFAULT_HITTABLE: dict = {
    "ImgScans" : 0,
    "ImgBans" : 0,
    "BanCount" : 0,
}

#General
client: commands.Bot = None
logger: Logger = None
databaseManager: FingerprintDataManager = None
pendingDatabaseManager: PendingDataManager = None
perfManager: PerformanceManager = None
imageManager: ImageManager = None
configDict: dict = {}
hitTable: dict = {}

#global Funcs

calcImageHashFunc = None
calcSHA256Func = None
calcEmbeddingFunc = None
