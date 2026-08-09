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

        self.imgConfigDict = globals.configDict["SaveImageConfig"]
        self.pendingDataManager = globals.pendingDatabaseManager

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

    def saveImage(self, imageBytes, imageSHA256 = None, imageEmbedd = None):
        if imageSHA256 == None:
            imageSHA256 = globals.calcSHA256Func(imageBytes)

        if self.exists(imageSHA256):
            logger.info("SHA256 - Image is already saved.")
            return

        if imageEmbedd == None:
            imageEmbedd = globals.calcEmbeddingFunc(imageBytes)

        #Hacky Solution for now... TODO Implement a search system within embedd check and or chunky search
        pendingTable = globals.pendingDatabaseManager.fetchAll("checks")
            
        threshold = globals.configDict["EmbeddingThreshold"]
        for value in pendingTable:
            if cosineSimilarity(imageEmbedd, value["embedding"]) >= threshold:
                logger.info("Embedding - Image is already saved.")
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
                break

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

    def getImage(self, sha256):
        for filename in os.listdir(self.savePath):
            filePath = os.path.join(self.savePath, filename)

            if not os.path.isfile(filePath):
                continue

            if not filename.endswith(".png"):
                continue

            nameSplit = filename.split("-")
            imageSHA256 = nameSplit.pop(3).replace(".png", "")
            if imageSHA256 == sha256:
                return (filename, filePath)

        return None

    def getImageList(self):
        result = {}
        for filename in os.listdir(self.savePath):## TODO make these loops unified into a func with filters
            filePath = os.path.join(self.savePath, filename)

            if not os.path.isfile(filePath):
                continue

            if not filename.endswith(".png"):
                continue

            nameSplit = filename.split("-")
            imageSHA256 = nameSplit.pop(3).replace(".png", "")
            date = nameSplit

            result[imageSHA256] = date

        return result

    def imageCount(self):
        result = 0
        for filename in os.listdir(self.savePath):
            filePath = os.path.join(self.savePath, filename)

            if not os.path.isfile(filePath):
                continue

            if not filename.endswith(".png"):
                continue

            result += 1
        return result


    