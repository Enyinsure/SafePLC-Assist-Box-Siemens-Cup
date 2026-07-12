from safeplc_assist_box.evidence.evidence_ranker import rank_evidence
from safeplc_assist_box.evidence.model_identity import reject_cross_family
from retrieval_test_support import evidence


def test_model_filter_runs_before_rrf_fusion():
    wrong = evidence("wrong", "CPU 1518-4 PN/DP front view X1", "CPU 1518-4 PN/DP", 2681, 0.99)
    wrong.metadata.update(retrieval_query="expanded", rank_within_query=1)
    right = evidence("right", "CPU 1517-3 PN/DP 前视图 PROFINET IO 接口 (X1)", page=2476, score=0.8)
    right.metadata.update(retrieval_query="expanded", rank_within_query=2)
    filtered = reject_cross_family([wrong, right], "CPU 1517-3 PN 的 X1 在哪里？")
    ranked = rank_evidence(filtered, "CPU 1517-3 PN 的 X1 在哪里？")
    assert [item.evidence_id for item in ranked] == ["right"]
    assert ranked[0].model_match_level == "exact_model"
