import os

from pathlib import Path
from logging import getLogger
from datetime import datetime, UTC
from enum import Enum

import globals

from utils.utils import dirCheck, getFiles
from utils.clipEmbedUtils import cosineSimilarity

logger = getLogger("ClankerMod")

class ImageManager():

    def __init__(self, savePath):
        self.savePath = savePath
        dirCheck(savePath)

        self.pendingDataManager = globals.pendingDatabaseManager

        self.MAX_KEEP_DAYS = globals.configDict["PendingKeepDays"]

    def exists(self, imageSHA256):
        for image in self.getImageList(True):
            if imageSHA256 in image["name"]:
                return True
        return False

    # Do not add embbed
    def saveImage(self, imageBytes, imageSHA256 = None) -> None:
        if imageSHA256 == None:
            imageSHA256 = globals.calcSHA256Func(imageBytes)

        if self.exists(imageSHA256):
            logger.info("SHA256 - Image is already saved.")
            return

        # Image Nameing date_imagesha.png
        timeDateNow = datetime.now(UTC).strftime("%Y-%m-%d")
        with open(f"{self.savePath}{timeDateNow}-{imageSHA256}.png", "wb") as f:
            f.write(imageBytes)

    def removeImage(self, imageSHA256) -> bool:
        for image in self.getImageList(True):

            if imageSHA256 in image["name"]:
                logger.info(f"Image {imageSHA256} has been deleted.")
                os.remove(filePath)
                return True
        return False

    def cleanup(self, force=False) -> None:
        timeDateNow = datetime.now(UTC).strftime("%Y-%m-%d").split("-")
        for image in self.getImageList(True):
            filename: str = image["name"]
            filePath: str = image["path"]

            if force:
                logger.info(f"Image cleanup {filename} has been deleted.")
                os.remove(filePath)
                continue

            nameSplit: list[str] = filename.split("-")
            dayDiff: int = abs(int(nameSplit[2]) - int(timeDateNow[2]))
            monthDiff: int = abs(int(nameSplit[1]) - int(timeDateNow[1]))

            totalDays: int = dayDiff + (monthDiff * 30)
            if totalDays >= self.MAX_KEEP_DAYS:
                logger.info(f"Image cleanup {filename} has been deleted kept for {totalDays}.")
                os.remove(filePath)

    def getImage(self, sha256: str):
        for image in self.getImageList(True):

            nameSplit = image["name"].split("-")
            imageSHA256 = nameSplit.pop(3).replace(".png", "")
            if imageSHA256 == sha256:
                return (image["name"], image["path"])

        return None

""" I was on something with this one.... TODO TEST THEN REMOVE.
    def getImageList(self) -> dict:
        result = {}
        for image in self.getImageList(True):

            nameSplit = image["name"].split("-")
            imageSHA256 = nameSplit.pop(3).replace(".png", "")
            date = nameSplit

            result[imageSHA256] = date

        return result
"""

    def imageCount(self) -> int: # The more i stare the more i hate this. Is this truly faster? Would i ever bother to find out?
        return len(self.getImageList(False))

    def getImageList(self, stream=False):
        result = []
        for filename in os.listdir(self.savePath):
            filePath = os.path.join(self.savePath, filename)

            if not os.path.isfile(filePath):
                continue

            if not filename.endswith(".png"):
                continue

            tempDict = {
                "name" : filename,
                "path" : filePath,
            }

            if stream:
                yield tempDict #Finally found use for yield. *Party poppers*
            else:
                result.append(tempDict)
        
        if not stream:
            return result


    