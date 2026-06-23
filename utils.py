import json
import os
import random

from pathlib import Path
from datetime import datetime, timedelta, UTC

#Strings
def limitString(msg, maxLength, end="..."): # TODO maybe check if special characters provide the incorrect sizeing. 
    if len(msg) >= maxLength + 2:
        return msg[:maxLength - (len(end) + 3)].rsplit(" ", 1)[0] + end
    return msg

#Json
def readJson(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}

def writeJson(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

#Hashing

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