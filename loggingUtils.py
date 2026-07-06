import logging

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

    logger = logging.getLogger("ClankerMod")#TODO look into which lib either FAISS CLIP or torch adding another logger and disable it.
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    consoleHandler = logging.StreamHandler()
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