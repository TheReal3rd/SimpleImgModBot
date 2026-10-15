import logging
import os 

from sys import stdout
from collections import deque
from datetime import datetime, UTC
from pathlib import Path
from logging import Logger
from logging.handlers import TimedRotatingFileHandler

import globals

logBuffer = deque(maxlen=500)

class MemoryHandler(logging.Handler):
    def emit(self, record):
        logBuffer.append(record)

def initLogging(): 
    global logBuffer

    logBuffer.clear()

    logger: Logger = logging.getLogger("ClankerMod")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    formatter = logging.Formatter(
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt = "%Y-%m-%d %H:%M:%S",
    )
    consoleHandler = logging.StreamHandler(stdout)
    consoleHandler.setFormatter(formatter)

    Path("logs").parent.mkdir(parents=True, exist_ok=True)
    timeDateNow = datetime.now(UTC).strftime("%Y-%m-%d")
    fileHandler = TimedRotatingFileHandler(
        f"logs/{timeDateNow}-clankerModLog.log",
        when = "midnight",
        interval = 1,
        backupCount = globals.configDict["MonthLogsCleanup"]
    )
    fileHandler.setFormatter(formatter)

    memoryHandler = MemoryHandler()

    logger.addHandler(fileHandler)
    logger.addHandler(consoleHandler)
    logger.addHandler(memoryHandler)

    return logger

def fetchLogs():
    global logBuffer
    result = ""
    for record in logBuffer:
        result += (f"{record.getMessage()}\n")
    return result
