import pytest

from redmine_rag.indexing.chunker import chunk_text


def test_chunk_text_splits_long_text() -> None:
    text = "A" * 2600

    chunks = chunk_text(text, target_chars=1000, overlap_chars=100)

    assert len(chunks) >= 3
    assert all(chunks)


def test_chunk_text_respects_overlap() -> None:
    text = "0123456789" * 40
    chunks = chunk_text(text, target_chars=100, overlap_chars=20)

    assert len(chunks) > 1
    assert chunks[0][-20:] == chunks[1][:20]


def test_chunk_text_handles_blank_and_invalid_args() -> None:
    assert chunk_text("   ") == []

    with pytest.raises(ValueError, match="target_chars"):
        chunk_text("abc", target_chars=0)

    with pytest.raises(ValueError, match="overlap_chars"):
        chunk_text("abc", overlap_chars=-1)
