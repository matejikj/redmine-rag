from __future__ import annotations

import re
from hashlib import sha1

import numpy as np

TOKEN_PATTERN = re.compile(r"\w+", flags=re.UNICODE)


def deterministic_embed_text(text: str, *, dim: int = 256) -> np.ndarray:
    """Deterministic local embedding baseline.

    Uses signed hashing over token and character n-gram features.
    This is intentionally lightweight and reproducible on laptop hardware.
    """

    if dim <= 0:
        raise ValueError("dim must be > 0")

    vector = np.zeros(dim, dtype=np.float32)
    normalized = text.lower().strip()
    if not normalized:
        return vector

    tokens = TOKEN_PATTERN.findall(normalized)
    for token in tokens:
        _add_hashed_feature(vector, f"tok:{token}", weight=1.0)

    compact = "".join(ch for ch in normalized if not ch.isspace())
    for index in range(len(compact) - 2):
        _add_hashed_feature(vector, f"tri:{compact[index : index + 3]}", weight=0.35)

    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


def _add_hashed_feature(vector: np.ndarray, feature: str, *, weight: float) -> None:
    digest = sha1(feature.encode("utf-8")).digest()
    bucket = int.from_bytes(digest[:4], byteorder="big", signed=False) % vector.shape[0]
    sign = 1.0 if (digest[4] % 2 == 0) else -1.0
    vector[bucket] += np.float32(sign * weight)
