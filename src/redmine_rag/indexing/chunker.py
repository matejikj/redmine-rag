from __future__ import annotations


def chunk_text(text: str, target_chars: int = 1200, overlap_chars: int = 150) -> list[str]:
    if not text.strip():
        return []
    if target_chars <= 0:
        raise ValueError("target_chars must be > 0")
    if overlap_chars < 0:
        raise ValueError("overlap_chars must be >= 0")

    chunks: list[str] = []
    step = max(target_chars - overlap_chars, 1)
    start = 0
    length = len(text)

    while start < length:
        end = min(start + target_chars, length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == length:
            break
        start += step

    return chunks
