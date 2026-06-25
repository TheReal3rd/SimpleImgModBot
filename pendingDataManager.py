import sqlite3
import numpy as np
import faiss

from enum import StrEnum

class Tables(StrEnum):
    CHECKS = "checks"
    BANS = "bans"

class PendingDataManager():

    def __init__(self, db_path: str = "pending.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS checks (
            msgID TEXT PRIMARY KEY,
            sha256 TEXT NOT NULL,
            embedding BLOB NOT NULL,
            time TEXT NOT NULL,
            messageID INT NOT NULL,
            channelID INT NOT NULL,
            userID INT NOT NULL
        )
        """)
        self.conn.commit()

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            msgID TEXT PRIMARY KEY,
            time TEXT NOT NULL,
            userID INT NOT NULL
        )
        """)
        self.conn.commit()

    @staticmethod
    def _serialize_embedding(embedding: np.ndarray) -> bytes:
        return embedding.astype(np.float32).tobytes()

    @staticmethod
    def _deserialize_embedding(blob: bytes) -> np.ndarray:
        return np.frombuffer(blob, dtype=np.float32)

    def tableIdentify(self, table):
        if isinstance(table, Tables):
            return table.name.lower()
        elif isinstance(table, str):
            return table.lower()
        else:
            return None

    def exists(self, table, msgID) -> bool:
        selectedTable = self.tableIdentify(table)
        if selectedTable == None:
            return False

        self.cursor.execute(
            f"SELECT 1 FROM {selectedTable} WHERE msgID = ?",
            (msgID,)
        )
        return self.cursor.fetchone() is not None

    def submitPending(self, table, dataDict):
        selectedTable = self.tableIdentify(table)
        if selectedTable == None:
            return False

        msgID = dataDict["msgID"]
        time = dataDict["time"]
        userID = dataDict["userID"]

        if self.exists(table, msgID):
            return False

        match(selectedTable):
            case "checks":
                sha256 = dataDict["sha256"]
                embedding = dataDict["embedding"]
                messageID = dataDict["messageID"]
                channelID = dataDict["channelID"]

                embedding = embedding.astype(np.float32)

                self.cursor.execute("""
                INSERT INTO checks (
                    msgID,
                    sha256,
                    embedding,
                    time,
                    messageID,
                    channelID,
                    userID
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(msgID),
                    sha256,
                    self._serialize_embedding(embedding),
                    time,
                    messageID,
                    channelID,
                    userID
                ))

            case "bans":
                self.cursor.execute("""
                INSERT INTO bans (
                    msgID,
                    time,
                    userID
                )
                VALUES (?, ?, ?)
                """, (
                    msgID,
                    time,
                    userID
                ))

        self.conn.commit()
        return True

    def get(self, table, msgID: str):
        selectedTable = self.tableIdentify(table)
        if selectedTable == None:
            return None

        match(selectedTable):
            case "checks":
                self.cursor.execute("""
                SELECT
                    msgID,
                    sha256,
                    embedding,
                    time,
                    messageID,
                    channelID,
                    userID
                FROM checks
                WHERE msgID = ?
                """, (msgID,))

                row = self.cursor.fetchone()

                if row is None:
                    return None

                return {
                    "msgID": row[0],
                    "sha256" : row[1],
                    "embedding": self._deserialize_embedding(row[2]),
                    "time": row[3],
                    "messageID": row[4],
                    "channelID" : row[5],
                    "userID" : row[6]
                }
            case "bans":
                self.cursor.execute("""
                SELECT
                    msgID,
                    time,
                    userID
                FROM bans
                WHERE msgID = ?
                """, (msgID,))

                row = self.cursor.fetchone()

                if row is None:
                    return None

                return {
                    "msgID": row[0],
                    "time": row[1],
                    "userID" : row[2]
                }


    def count(self, table) -> int:
        selectedTable = self.tableIdentify(table)
        if selectedTable == None:
            return -1

        self.cursor.execute(
            f"SELECT COUNT(*) FROM {selectedTable}"
        )
        return self.cursor.fetchone()[0]


    def fetchAll(self, table):
        selectedTable = self.tableIdentify(table)
        if selectedTable == None:
            return None

        match(selectedTable):
            case "checks":
                self.cursor.execute("""
                SELECT
                    msgID,
                    sha256,
                    embedding,
                    time,
                    messageID,
                    channelID,
                    userID
                FROM checks
                """)

                rows = self.cursor.fetchall()

                return [
                    {
                        "msgID": row[0],
                        "sha256": row[1],
                        "embedding": self._deserialize_embedding(row[2]),
                        "time": row[3],
                        "messageID": row[4],
                        "channelID" : row[5],
                        "userID" : row[6]
                    }
                    for row in rows
                ]
            case "bans":
                self.cursor.execute("""
                SELECT
                    msgID,
                    time,
                    userID
                FROM bans
                """)

                rows = self.cursor.fetchall()

                return [
                    {
                        "msgID": row[0],
                        "time": row[1],
                        "userID" : row[2]
                    }
                    for row in rows
                ]
        return None

    def deleteEntry(self, table, msgID:str):
        selectedTable = self.tableIdentify(table)
        if selectedTable == None:
            return None

        dbSizeBefore = self.count(table)

        self.cursor.execute(f"""
        DELETE FROM {selectedTable} WHERE msgID = ?
        """, (msgID,))
        self.conn.commit()

        return {
            "before" : dbSizeBefore,
            "after" : self.count(table)
        }

    def close(self):
        self.conn.close()

    def __len__(self):
        total = 0
        for table in Tables:
            total += self.count(table)
        return total


if __name__ == "__main__":
    import os

    testDB = PendingDataManager("test.db")

    print(testDB.tableIdentify(Tables.BANS))

    print(testDB.submitPending(Tables.BANS, {"msgID" : "10000",  "time" : "timeDate", "userID" : 1000}))

    print(testDB.fetchAll(Tables.BANS))

    print(testDB.deleteEntry(Tables.BANS, "10000"))

    print(testDB.fetchAll(Tables.BANS))

    os.remove("test.db")