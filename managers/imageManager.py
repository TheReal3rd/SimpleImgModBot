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

    def exists(self, imageSHA256) -> bool:
        for image in self.getImageStream():
            if imageSHA256 in image["name"]:
                return True
        return False

    # Do not add embbed
    def saveImage(self, imageBytes, imageSHA256:str = "") -> None:
        if imageSHA256 == None or imageSHA256 == "":
            imageSHA256 = globals.calcSHA256Func(imageBytes)

        if self.exists(imageSHA256):
            logger.info("SHA256 - Image is already saved.")
            return

        # Image Nameing date_imagesha.png
        timeDateNow = datetime.now(UTC).strftime("%Y-%m-%d")
        with open(f"{self.savePath}{timeDateNow}-{imageSHA256}.png", "wb") as f:
            f.write(imageBytes)

    def removeImage(self, imageSHA256) -> bool:
        for image in self.getImageStream():

            if imageSHA256 in image["name"]:
                logger.info(f"Image {imageSHA256} has been deleted.")
                os.remove(image["path"])
                return True
        return False

    def cleanup(self, force=False) -> None:
        timeDateNow = datetime.now(UTC).strftime("%Y-%m-%d").split("-")
        for image in self.getImageStream():
            filename: str = image["name"]
            filePath: str = image["path"]

            if force:
                logger.info(f"Image cleanup {filename} has been deleted.")
                os.remove(filePath)
                continue

            nameSplit: list[str] = filename.replace(".png", "").split("-")
            dayDiff: int = abs(int(nameSplit[2]) - int(timeDateNow[2]))
            monthDiff: int = abs(int(nameSplit[1]) - int(timeDateNow[1]))
            yearDiff: int = abs(int(nameSplit[0]) - int(timeDateNow[0]))

            totalDays: int = dayDiff + (monthDiff * 30) + (yearDiff * 365)
            if totalDays >= self.MAX_KEEP_DAYS:
                logger.info(f"Image cleanup {filename} has been deleted kept for {totalDays}.")
                os.remove(filePath)

    def getImage(self, sha256: str) -> tuple:
        for image in self.getImageStream():

            nameSplit = image["name"].split("-")

            if len(nameSplit) != 3:
                logger.warning(f"Abnormal file name structure of {image["name"]}. Unable to parse.")
                continue

            imageSHA256 = nameSplit.pop(3).replace(".png", "")
            if imageSHA256 == sha256:
                return (image["name"], image["path"])

        return ()

    def imageCount(self) -> int:
        return len(self.getImageList())

    def getImageStream(self) -> dict:
        for filename in os.listdir(self.savePath):
            filePath = os.path.join(self.savePath, filename)

            if not os.path.isfile(filePath):
                continue

            if not filename.endswith(".png"):
                continue

            nameSplit = filename.split("-")
            imageSHA256 = nameSplit.pop(3).replace(".png", "")
            date = nameSplit

            tempDict = {
                "name" : filename,
                "path" : filePath,
                "sha" : imageSHA256,
                "date" : date,
            }

            yield tempDict #Finally found use for yield. *Party poppers*
  
    def getImageList(self) -> list:
        result = []
        for img in self.getImageStream(): 
            result.append(img)
        return result


    