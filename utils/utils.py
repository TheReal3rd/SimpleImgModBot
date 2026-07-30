import os

from pathlib import Path
from datetime import datetime, timedelta, UTC
from logging import getLogger
from json import load, dump, JSONDecodeError

import globals

logger = getLogger("ClankerMod")

#Strings
def limitString(msg, maxLength, end="..."):
    if len(msg) >= maxLength + 2:
        return msg[:maxLength - (len(end) + 3)].rsplit(" ", 1)[0] + end
    return msg

def pageString(text, maxLength):
    lines = text.splitlines(keepends=True)
    pages = []
    workingPage = ""

    for line in lines:
        lineLength = len(line)
        workPageLength = len(workingPage)

        if len(workingPage) >= maxLength:
            pages.append(workingPage)
            workingPage = ""

        else:
            workingPage += line

    return pages

#Json
def readJson(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            resultData = load(f)

            for defaultkey in default.keys():
                if not defaultkey in resultData.keys():
                    resultData[defaultkey] = default[defaultkey]
                    
            return resultData
    except (FileNotFoundError, JSONDecodeError):
        return default if default is not None else {}

def writeJson(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        dump(data, f, indent=4, ensure_ascii=False)

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
    return datetime.now(UTC) >= startTime + timedelta(days=days)

def loadImageFolder(folderPath):
    for filename in os.listdir(folderPath):
        filePath = os.path.join(folderPath, filename)
        if not os.path.isfile(filePath):
            continue

        correctFormat = False
        for ext in globals.IMG_EXTENSIONS:
            if filename.endswith(ext):
                correctFormat = True
                break

        if not correctFormat:
            continue

        try:
            imageData = None
            with open(filePath, "rb") as f:
                imageData = f.read()

            sha, emb = globals.calcImageHashFunc(imageData)
            if globals.databaseManager.add(sha, emb):
                logger.info(f"Image added to database: {filename}")

                if not globals.configDict["Debug"]:#To prevent images being deleted and lost while in development.
                    os.remove(filePath)
                    logger.warning(f"Image deleted {filePath}")
            else:
                logger.warning(f"Failed to add {filename} to the database...")
        except Exception as e:
            logger.error(f"Failed to process image: {filename} | {e}")