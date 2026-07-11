from safeplc_assist_box.evidence.evidence_pool import SharedEvidencePool
from safeplc_assist_box.schemas import AgentEvidence


def test_evidence_pool_deduplicates_and_tracks_agents():
    pool = SharedEvidencePool()
    ev = AgentEvidence("ev1", "src", "sample", "text", "same text", page=1)
    id1 = pool.add(ev, "Parameter Agent", "claim a")
    id2 = pool.add(AgentEvidence("ev2", "src", "sample", "text", "same text", page=1), "Figure Agent", "claim b")
    assert id1 == id2
    item = pool.get(id1)
    assert set(item.agent_names) == {"Parameter Agent", "Figure Agent"}
    assert len(pool.list()) == 1

