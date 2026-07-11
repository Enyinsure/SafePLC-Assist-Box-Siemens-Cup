from safeplc_assist_box.tools.chroma_text_retriever import ChromaTextRetriever, ChromaUnavailable


def test_text_chroma_retrieval_requires_existing_directory(tmp_path):
    retriever = ChromaTextRetriever(str(tmp_path / "missing"))
    assert not retriever.available()
    try:
        retriever.discover()
    except ChromaUnavailable as exc:
        assert "does not exist" in str(exc)
    else:
        raise AssertionError("missing Chroma directory should not be silently accepted")
