from retrieval_test_support import evidence
from safeplc_assist_box.evidence.evidence_ranker import rank_evidence


def _retrieval(item, query, rank):
    item.metadata.update({"retrieval_query": query, "rank_within_query": rank})
    return item


def test_emc_rrf_promotes_installation_measures():
    original = "EMC 安装时接地和屏蔽需要注意什么？"
    expanded = "grounded control cabinets noise filters supply lines EMC"
    correct_text = "Electromagnetic compatibility. grounded control cabinets/control boxes; noise filters in the supply lines."
    candidates = [
        _retrieval(evidence("cert", "EMC certification and approvals for communication module", score=0.98), original, 1),
        _retrieval(evidence("install", correct_text, score=0.55), original, 8),
        _retrieval(evidence("install", correct_text, score=0.65), expanded, 1),
    ]
    ranked = rank_evidence(candidates, query=original)
    assert ranked[0].evidence_id == "install"
    assert ranked[0].matched_query_count == 2
