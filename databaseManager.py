import sqlite3
import numpy as np
import faiss

# Entirely AI.
# 

class DatabaseManager:

    def __init__(self, db_path="fingerprints.db", dim=512):
        self.db_path = db_path
        self.dim = dim

        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sha256 TEXT UNIQUE,
            phash TEXT,
            embedding BLOB
        )
        """)
        self.conn.commit()

        self.index = faiss.IndexFlatIP(self.dim)
        self.id_map = []
        self._load_all()

    def _serialize(self, vec: np.ndarray):
        return vec.astype("float32").tobytes()

    def _deserialize(self, blob):
        return np.frombuffer(blob, dtype="float32")

    def add(self, sha256: str, phash: str, embedding: np.ndarray):
        self.cursor.execute("""
        INSERT OR IGNORE INTO fingerprints (sha256, phash, embedding)
        VALUES (?, ?, ?)
        """, (
            sha256,
            phash,
            self._serialize(embedding)
        ))

        self.conn.commit()

        # add to FAISS
        self.index.add(np.array([embedding.astype("float32")]))
        self.id_map.append(sha256)

    def get_by_sha256(self, sha256: str):
        self.cursor.execute("""
        SELECT sha256, phash, embedding
        FROM fingerprints
        WHERE sha256 = ?
        """, (sha256,))

        row = self.cursor.fetchone()

        if not row:
            return None

        return {
            "sha256": row[0],
            "phash": row[1],
            "embedding": self._deserialize(row[2])
        }

    def fetch_all(self):
        self.cursor.execute("""
        SELECT sha256, phash, embedding
        FROM fingerprints
        """)

        rows = self.cursor.fetchall()

        return [
            {
                "sha256": r[0],
                "phash": r[1],
                "embedding": self._deserialize(r[2])
            }
            for r in rows
        ]

    def search(self, embedding: np.ndarray, top_k=5):
        if len(self.id_map) == 0:
            return []

        D, I = self.index.search(
            np.array([embedding.astype("float32")]),
            top_k
        )

        results = []

        for score, idx in zip(D[0], I[0]):
            if idx < len(self.id_map):
                sha = self.id_map[idx]

                self.cursor.execute("""
                SELECT sha256, phash, embedding
                FROM fingerprints
                WHERE sha256 = ?
                """, (sha,))

                row = self.cursor.fetchone()

                if row:
                    results.append({
                        "score": float(score),
                        "sha256": row[0],
                        "phash": row[1],
                        "embedding": self._deserialize(row[2])
                    })

        return results

    def _load_all(self):
        self.cursor.execute("""
        SELECT sha256, embedding
        FROM fingerprints
        """)

        rows = self.cursor.fetchall()

        if not rows:
            return

        vectors = []

        for sha, emb_blob in rows:
            vec = self._deserialize(emb_blob)
            vectors.append(vec)
            self.id_map.append(sha)

        if vectors:
            self.index.add(np.array(vectors, dtype="float32"))