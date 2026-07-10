from enum import StrEnum

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

DEFAULT_CONFIG = {
    "ServerID" : "",
    "ChannelID" : "",
    "Token" : "",
    "EmbeddingThreshold" : 0.87,
    "Debug" : False, # Disables Kick, Ban and image deletions for db calls used to test whether the operations reach them.
    "ClipProcessor" : "auto",
    "JokesMemes" : False, # Adding this so if someone does use this they can disable my joke out of the bot. 
    "RequiredRoleID" : "", #role id. Replace this with one for your server.
    "Twitch": {
        "TwitchChannel": "",  # Twitch channel log-in name of the channel you want live notifications for
        "TokenCache": "", # filepath to a json file containing the OAuth tokens
        "AppId": "",  # Twitch App ID.
        "AppSecret": "",  # Twitch App Secret
        "NotifChannel": "",  # Discord channel ID you want the bot to send the notifications on
        "NotifRole": ""  # Role you want the bot to ping. Do not include the '@'
    },
    "MonthLogsCleanup" : 2, # The Duration for how long logs will be kept. In Months
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
configDict = {}
hitTable = {}

#global Funcs

calcImageHashFunc = None
calcSHA256Func = None
calcEmbeddingFunc = None

class PendingType(StrEnum):
    IMAGE_BAN = "imageBan"
    USER_BAN = "userBan"
    ROLE_USER_BAN = "roleUserBan"

