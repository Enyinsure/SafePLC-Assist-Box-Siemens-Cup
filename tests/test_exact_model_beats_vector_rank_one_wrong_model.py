from safeplc_assist_box.evidence.evidence_ranker import rank_evidence
from safeplc_assist_box.evidence.model_identity import reject_cross_family
from retrieval_test_support import evidence


def test_exact_model_beats_vector_rank_one_wrong_model():
    wrong = evidence("wrong", "CPU 1518-4 PN/DP front view X1", "CPU 1518-4 PN/DP", 2681, 0.99)
    right = evidence(
        "right", "图 2-237 不带前面板的 CPU 1517-3 PN/DP 的前视图；PROFINET IO 接口 (X1)",
        page=2476, score=0.75, manual_figure_number="图 2-237",
    )
    wrong.metadata.update(retrieval_query="expanded", rank_within_query=1)
    right.metadata.update(retrieval_query="expanded", rank_within_query=2, location_marker="⑦")
    result = rank_evidence(reject_cross_family([wrong, right], "CPU 1517-3 PN 的 X1 在哪里？"), "CPU 1517-3 PN 的 X1 在哪里？")
    assert result[0].page == 2476
    assert all(item.page != 2681 for item in result)
