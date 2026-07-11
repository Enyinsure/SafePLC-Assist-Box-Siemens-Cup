from safeplc_assist_box.agents.orchestrator import run_agent_system


def test_no_silent_full_fallback(monkeypatch):
    for key in [
        "SAFEPLC_CHROMA_DIR",
        "SAFEPLC_CHUNKS_JSONL",
        "SAFEPLC_PAGES_JSONL",
        "SAFEPLC_ALLOW_JSONL_FALLBACK",
    ]:
        monkeypatch.delenv(key, raising=False)
    response = run_agent_system("CPU 1517-3 PN 的 X1 接口在哪里？", mode="FULL")
    assert response.mode == "FULL"
    assert response.evidence_pool.evidences == []
    assert response.verdict == "NEED_MORE_EVIDENCE"
    assert any("SAMPLE evidence was not used" in warning for warning in response.warnings)
