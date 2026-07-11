from safeplc_assist_box.config import SafePLCConfig
from safeplc_assist_box.schemas import AgentEvidence
from safeplc_assist_box.tools.tool_registry import ToolRegistry


def evidence(backend, score):
    return AgentEvidence(
        evidence_id=f"{backend}-{score}",
        source=backend,
        source_type="test",
        modality="text",
        text="CPU 1517-3 PN X1 evidence",
        retrieval_backend=backend,
        normalized_score=score,
        retrieval_score=score,
        module_model="CPU 1517-3 PN/DP",
    )


class FakeRetriever:
    def __init__(self, records):
        self.records = records
        self.calls = 0

    def available(self):
        return True

    def search(self, query, top_k=8, modalities=None):
        self.calls += 1
        return list(self.records)


def registry(monkeypatch, chroma_records, jsonl_records, hybrid=False, min_score="0.20"):
    monkeypatch.setenv("SAFEPLC_ALLOW_JSONL_FALLBACK", "1")
    monkeypatch.setenv("SAFEPLC_ENABLE_JSONL_HYBRID", "1" if hybrid else "0")
    monkeypatch.setenv("SAFEPLC_JSONL_FALLBACK_MIN_SCORE", min_score)
    config = SafePLCConfig.from_env(mode="FULL")
    tool_registry = ToolRegistry(config)
    tool_registry._text_retriever = FakeRetriever(chroma_records)
    tool_registry._jsonl_chunks = FakeRetriever(jsonl_records)
    tool_registry._jsonl_pages = None
    return tool_registry
