from enum import IntEnum, StrEnum

class PendingType(StrEnum):
    IMAGE_BAN = "imageBan"
    USER_BAN = "userBan"
    ROLE_USER_BAN = "roleUserBan"

class ImageSaveModes(IntEnum):
    BASIC = 0
    SHA = 1
    EMBBED = 2
    ALL = 3

#Const
SERVER_ID = -1
CHANNEL_ID = -1

RESENFOR_ID = 332634195941654529
REGIONAL_L = "\U0001F1F1"
MAXIMUM_L = 30 # So im not constantly oblitarating him.

THUMB_UP = "\U0001F44D"

MSG_LEN_LIMIT = 2000
EMBED_LEN_LIMIT = 4095
SHA256_CHAR_LEN = 64
SCAN_BATCH_SIZE = 15
IMG_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif", ".heic", ".heif", ".avif", ".jfif",] 
# Few formats aren't included due to not working with current set up nor scope.

CONFIG_PATH = "config.json"
IMAGE_PATH = "working_images/"

DEFAULT_CONFIG = {
    "ServerID" : "",
    "ChannelID" : "",
    "Token" : "",
    "EmbeddingThreshold" : 0.87,
    "Debug" : False, # Disables Kick, Ban and image deletions for db calls used to test whether the operations reach them.
    "ClipProcessor" : "auto",
    "JokesMemes" : True, # Adding this so if someone does use this they can disable my joke out of the bot. 
    "RequiredRoleID" : "", #role id. Replace this with one for your server.
    "Twitch": {
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
    "SaveImageConfig" : {
        "KeepDays" : 20, # TODO remove the keep and unify with pending keep days.
        # 0 - BASIC - Save images that aren't banned.
        # 1 - SHA - Save images that got hit by SHA256 check.
        # 2 - EMBBED- Save images that got hit by embbed check.
        # 3 - ALL - Save Everything.
        "SaveLevel": ImageSaveModes.ALL
    }
}

ABT_MSG = [
    "4d61646520627920337264",
    "Resenfor Smells.",
    "Dargo is a cutie pie! :3",
    "Andromeda show me ur package.",
    "Tin Tin is a cootie. :3",
    "Resenfor is sometimes cute.",
    "E",
    "3.1415926535",
]

HITS_PATH = "hits.json" # Was only for Resenfor react but used to store other useful data.
DEFAULT_HITTABLE = {
    "Img_Scans" : 0,
    "Img_Bans" : 0,
    "BanCount" : 0,
}

#General
client = None
logger = None
databaseManager = None
pendingDatabaseManager = None
perfManager = None
imageManager = None
configDict = {}
hitTable = {}

#global Funcs

calcImageHashFunc = None
calcSHA256Func = None
calcEmbeddingFunc = None
