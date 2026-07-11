from safeplc_assist_box.evidence.evidence_pool import SharedEvidencePool
from safeplc_assist_box.schemas import AgentEvidence


def test_same_page_chunk_deduplication():
    pool = SharedEvidencePool()
    page = AgentEvidence(
        "page", "manual", "manual", "text", "CPU X1 interface location and front view marker details", page=10, document_id="doc"
    )
    chunk = AgentEvidence(
        "chunk", "manual", "manual", "text", "X1 interface location and front view marker details", page=10, document_id="doc", chunk_id="c1"
    )
    assert pool.add(page, "Figure Agent") == pool.add(chunk, "Figure Agent")
    assert len(pool.list()) == 1
    assert pool.list()[0].metadata["dedup_reason"] == "same_document_page_overlapping_text"
