from enum import StrEnum

#Const
SERVER_ID = -1
CHANNEL_ID = -1

RESENFOR_ID = 332634195941654529

MSG_LEN_LIMIT = 2000
EMBED_LEN_LIMIT = 4095
SHA256_CHAR_LEN = 64
SCAN_BATCH_SIZE = 15
IMG_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif", ".heic", ".heif", ".avif", ".jfif",] 
# Few formats aren't included due to not working with current set up nor scope.

CONFIG_PATH = "config.json"

#TODO change all configs snake case to camel case not sure why i did that...
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