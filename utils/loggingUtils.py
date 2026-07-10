import logging
import os 

from sys import stdout
from collections import deque
from datetime import datetime, UTC
from pathlib import Path

import globals

logBuffer = deque(maxlen=500)

class MemoryHandler(logging.Handler):
    def emit(self, record):
        logBuffer.append(record)

def initLogging():
    global logBuffer
    logger = logging.getLogger("ClankerMod")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt = "%Y-%m-%d %H:%M:%S",
    )
    consoleHandler = logging.StreamHandler(stdout)
    consoleHandler.setFormatter(formatter)

    Path("logs").parent.mkdir(parents=True, exist_ok=True)
    timeDateNow = datetime.now(UTC).strftime("%Y-%m-%d")
    fileHandler = logging.FileHandler(f"logs/{timeDateNow}-clankerModLog.log", encoding="utf-8")
    fileHandler.setFormatter(formatter)

    memoryHandler = MemoryHandler()

    logger.addHandler(fileHandler)
    logger.addHandler(consoleHandler)
    logger.addHandler(memoryHandler)

    logCleanup("logs")
    return logger

def fetchLogs():
    global logBuffer
    result = ""
    for record in logBuffer:
        result += (f"{record.getMessage()}\n")
    return result

def logCleanup(folderPath):
    timeDateNow = datetime.now(UTC).strftime("%Y-%m-%d").split("-")
    for filename in os.listdir(folderPath):
        filePath = os.path.join(folderPath, filename)
        if not os.path.isfile(filePath):
            continue

        if not filename.endswith(".log"):
            continue

        nameSplit = filename.split("-")
        monthDiff = abs(int(nameSplit[1]) - int(timeDateNow[1]))
        yearDiff = abs(int(nameSplit[0]) - int(timeDateNow[0]))#Kinda useless unless the bot sits idle for a whole year with no restarts. But ah should be fine.

        monthMaxDura = globals.configDict["MonthLogsCleanup"]
        YEAR_MAX_DURA = 1

        if yearDiff >= YEAR_MAX_DURA or monthDiff >= monthMaxDura:
            logger.info(f"Log cleanup {filename} has been deleted.")
            os.remove(filePath)