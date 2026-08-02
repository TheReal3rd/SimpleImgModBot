import os

from pathlib import Path
from logging import getLogger
from datetime import datetime, UTC
from enum import Enum

import globals

from utils.utils import dirCheck, getFiles

logger = getLogger("ClankerMod")

class ImageManager():

    def __init__(self, savePath):
        self.savePath = savePath
        dirCheck(savePath)

        self.imgConfigDict = globals.configDict["SaveImageConfig"]

    def getSaveLevel(self):
        return self.imgConfigDict["SaveLevel"]

    def exists(self, imageSHA256):
        for filename in os.listdir(self.savePath):
            filePath = os.path.join(self.savePath, filename)

            if not os.path.isfile(filePath):
                continue

            if not filename.endswith(".png"):
                continue

            if imageSHA256 in filename:
                return True
        return False

    def saveImage(self, imageBytes, imageSHA256 = None):
        if imageSHA256 == None:
            imageSHA256 = globals.calcSHA256Func(imageBytes)

        if self.exists(imageSHA256):
            logger.info("Image is already saved.")
            return

        # Image Nameing date_imagesha.png
        timeDateNow = datetime.now(UTC).strftime("%Y-%m-%d")
        with open(f"{self.savePath}{timeDateNow}-{imageSHA256}.png", "wb") as f:
            f.write(imageBytes)

    def removeImage(self, imageSHA256):
        for filename in os.listdir(self.savePath):
            filePath = os.path.join(self.savePath, filename)

            if not os.path.isfile(filePath):
                continue

            if not filename.endswith(".png"):
                continue

            if imageSHA256 in filename:
                logger.info(f"Image {filename} has been deleted.")
                os.remove(filePath)

    def cleanup(self, force=False):
        timeDateNow = datetime.now(UTC).strftime("%Y-%m-%d").split("-")
        for filename in os.listdir(self.savePath):
            filePath = os.path.join(self.savePath, filename)

            if not os.path.isfile(filePath):
                continue

            if not filename.endswith(".png"):
                continue

            if force:
                logger.info(f"Image cleanup {filename} has been deleted.")
                os.remove(filePath)
                continue

            nameSplit = filename.split("-")
            monthDiff = abs(int(nameSplit[1]) - int(timeDateNow[1]))
            yearDiff = abs(int(nameSplit[0]) - int(timeDateNow[0]))

            monthMaxDura = self.imgConfigDict["KeepDays"]
            YEAR_MAX_DURA = 1

            if yearDiff >= YEAR_MAX_DURA or monthDiff >= monthMaxDura:
                logger.info(f"Image cleanup {filename} has been deleted.")
                os.remove(filePath)


    