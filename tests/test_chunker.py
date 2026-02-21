from redmine_rag.indexing.chunker import chunk_text


def test_chunk_text_splits_long_text() -> None:
    text = "A" * 2600

    chunks = chunk_text(text, target_chars=1000, overlap_chars=100)

    assert len(chunks) >= 3
    assert all(chunks)
