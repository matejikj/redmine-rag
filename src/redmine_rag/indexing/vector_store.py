from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import numpy as np


@dataclass(slots=True)
class VectorHit:
    key: str
    score: float


class LocalNumpyVectorStore:
    """Small-footprint local vector store for early-stage development.

    This baseline uses cosine similarity over a normalized matrix.
    It is sufficient for low/medium scale on a laptop and can be replaced later.
    """

    def __init__(self, index_path: str, meta_path: str) -> None:
        self.index_path = Path(index_path)
        self.meta_path = Path(meta_path)
        self._matrix = np.empty((0, 0), dtype=np.float32)
        self._keys: list[str] = []
        self._load()

    def _load(self) -> None:
        if self.index_path.exists() and self.meta_path.exists():
            with self.index_path.open("rb") as fp:
                self._matrix = np.load(fp)
            self._keys = json.loads(self.meta_path.read_text(encoding="utf-8"))

    def save(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.meta_path.parent.mkdir(parents=True, exist_ok=True)
        with self.index_path.open("wb") as fp:
            np.save(fp, self._matrix)
        self.meta_path.write_text(json.dumps(self._keys), encoding="utf-8")

    def clear(self) -> None:
        self._matrix = np.empty((0, 0), dtype=np.float32)
        self._keys = []

    @property
    def keys(self) -> tuple[str, ...]:
        return tuple(self._keys)

    def upsert(self, key: str, vector: np.ndarray) -> None:
        vec = self._normalize(vector.astype(np.float32))

        if self._matrix.size == 0:
            self._matrix = vec.reshape(1, -1)
            self._keys = [key]
            return

        if vec.shape[0] != self._matrix.shape[1]:
            raise ValueError("Vector dimension mismatch")

        if key in self._keys:
            idx = self._keys.index(key)
            self._matrix[idx] = vec
        else:
            self._keys.append(key)
            self._matrix = np.vstack([self._matrix, vec])

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> list[VectorHit]:
        if self._matrix.size == 0:
            return []

        q = self._normalize(query_vector.astype(np.float32))
        if q.shape[0] != self._matrix.shape[1]:
            raise ValueError("Query vector dimension mismatch")

        scores = self._matrix @ q
        top_indices = np.argsort(-scores)[:top_k]

        return [
            VectorHit(key=self._keys[index], score=float(scores[index]))
            for index in top_indices
            if scores[index] > 0
        ]

    def remove_keys_not_in(self, allowed_keys: set[str]) -> int:
        if not self._keys:
            return 0

        keep_indices = [idx for idx, key in enumerate(self._keys) if key in allowed_keys]
        removed = len(self._keys) - len(keep_indices)
        if removed == 0:
            return 0

        self._keys = [self._keys[idx] for idx in keep_indices]
        if keep_indices:
            self._matrix = self._matrix[keep_indices]
        else:
            self._matrix = np.empty((0, 0), dtype=np.float32)
        return removed

    @staticmethod
    def _normalize(vector: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return cast(np.ndarray, vector / norm)
