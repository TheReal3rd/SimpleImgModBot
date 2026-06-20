import sqlite3
import numpy as np
import faiss

#Entirely AI generated.

class DatabaseManager:

    def __init__(self, db_path: str = "fingerprints.db", embedding_dim: int = 512):
        self.db_path = db_path
        self.embedding_dim = embedding_dim

        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS fingerprints (
            sha256 TEXT PRIMARY KEY,
            phash TEXT NOT NULL,
            embedding BLOB NOT NULL
        )
        """)
        self.conn.commit()

        # cosine similarity index
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.sha_map = []
        self.rebuild_index()

    @staticmethod
    def _serialize_embedding(embedding: np.ndarray) -> bytes:
        return embedding.astype(np.float32).tobytes()

    @staticmethod
    def _deserialize_embedding(blob: bytes) -> np.ndarray:
        return np.frombuffer(blob, dtype=np.float32)

    def exists(self, sha256: str) -> bool:
        self.cursor.execute(
            "SELECT 1 FROM fingerprints WHERE sha256 = ?",
            (sha256,)
        )
        return self.cursor.fetchone() is not None

    def add(self, sha256: str, phash: str, embedding: np.ndarray) -> bool:
        if self.exists(sha256):
            return False

        embedding = embedding.astype(np.float32)

        self.cursor.execute("""
        INSERT INTO fingerprints (
            sha256,
            phash,
            embedding
        )
        VALUES (?, ?, ?)
        """, (
            sha256,
            phash,
            self._serialize_embedding(embedding)
        ))

        self.conn.commit()

        self.index.add(np.array([embedding], dtype=np.float32))
        self.sha_map.append(sha256)

        return True

    def get(self, sha256: str):
        self.cursor.execute("""
        SELECT
            sha256,
            phash,
            embedding
        FROM fingerprints
        WHERE sha256 = ?
        """, (sha256,))

        row = self.cursor.fetchone()

        if row is None:
            return None

        return {
            "sha256": row[0],
            "phash": row[1],
            "embedding": self._deserialize_embedding(row[2])
        }

    def count(self) -> int:
        self.cursor.execute(
            "SELECT COUNT(*) FROM fingerprints"
        )
        return self.cursor.fetchone()[0]

    def fetch_all(self):
        self.cursor.execute("""
        SELECT
            sha256,
            phash,
            embedding
        FROM fingerprints
        """)

        rows = self.cursor.fetchall()

        return [
            {
                "sha256": row[0],
                "phash": row[1],
                "embedding": self._deserialize_embedding(row[2])
            }
            for row in rows
        ]

    def search(self, embedding: np.ndarray, top_k: int = 5):
        if not self.sha_map:
            return []

        embedding = embedding.astype(np.float32)

        k = min(top_k, len(self.sha_map))

        distances, indices = self.index.search(
            np.array([embedding], dtype=np.float32),
            k
        )

        results = []

        for score, idx in zip(distances[0], indices[0]):

            if idx < 0:
                continue

            sha256 = self.sha_map[idx]

            self.cursor.execute("""
            SELECT
                sha256,
                phash
            FROM fingerprints
            WHERE sha256 = ?
            """, (sha256,))

            row = self.cursor.fetchone()

            if row:
                results.append({
                    "score": float(score),
                    "sha256": row[0],
                    "phash": row[1]
                })

        return results

    def rebuild_index(self):
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.sha_map = []

        self.cursor.execute("""
        SELECT
            sha256,
            embedding
        FROM fingerprints
        """)

        rows = self.cursor.fetchall()

        if not rows:
            return

        embeddings = []

        for sha256, blob in rows:
            embeddings.append(
                self._deserialize_embedding(blob)
            )
            self.sha_map.append(sha256)

        self.index.add(
            np.array(
                embeddings,
                dtype=np.float32
            )
        )

    def close(self):
        self.conn.close()

    def __len__(self):
        return self.count()