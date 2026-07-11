from safeplc_assist_box.evidence.evidence_pool import SharedEvidencePool
from safeplc_assist_box.schemas import AgentEvidence


def test_chroma_jsonl_deduplication():
    pool = SharedEvidencePool()
    chroma = AgentEvidence("c", "manual", "manual", "text", "X1 is on the lower front panel", retrieval_backend="chroma_text", page=5)
    jsonl = AgentEvidence("j", "manual", "manual", "text", "X1 is on the lower front panel.", retrieval_backend="jsonl_pages", page=5)
    assert pool.add(chroma, "Figure Agent") == pool.add(jsonl, "Figure Agent")
    assert set(pool.list()[0].metadata["merged_backends"]) == {"chroma_text", "jsonl_pages"}
