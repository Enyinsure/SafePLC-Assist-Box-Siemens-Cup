import json

from safeplc_assist_box.config import SafePLCConfig
from safeplc_assist_box.tools.tool_registry import ToolRegistry


def test_jsonl_fallback_is_used_only_when_explicit(monkeypatch, tmp_path):
    chunks = tmp_path / "chunks.jsonl"
    chunks.write_text(json.dumps({"text": "CPU 1517 X1 PROFINET evidence", "page": 2476, "modality": "text"}) + "\n", encoding="utf-8")
    monkeypatch.setenv("SAFEPLC_ALLOW_JSONL_FALLBACK", "1")
    monkeypatch.setenv("SAFEPLC_CHUNKS_JSONL", str(chunks))
    registry = ToolRegistry(SafePLCConfig.from_env(mode="FULL"))
    rows = registry.search_text("CPU 1517 X1 PROFINET", top_k=2)
    assert rows
    assert rows[0].retrieval_backend == "jsonl_chunks"
