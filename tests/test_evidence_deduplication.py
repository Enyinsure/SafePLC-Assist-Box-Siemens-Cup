from safeplc_assist_box.evidence.evidence_pool import SharedEvidencePool
from safeplc_assist_box.schemas import AgentEvidence


def test_evidence_deduplication_same_page_chunk():
    pool = SharedEvidencePool()
    a = AgentEvidence("", "manual", "jsonl", "text", "same evidence text " * 20, page=10, chunk_id="c1")
    b = AgentEvidence("", "manual", "jsonl", "text", "same evidence text " * 20, page=10, chunk_id="c2")
    id1 = pool.add(a, "A", "claim1")
    id2 = pool.add(b, "B", "claim2")
    assert id1 == id2
    assert len(pool.list()) == 1
