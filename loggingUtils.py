import logging

from sys import stdout
from collections import deque
from datetime import datetime, UTC
from pathlib import Path

from utils import logCleanup

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