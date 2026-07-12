from safeplc_assist_box.evidence.evidence_ranker import location_directness_score
from retrieval_test_support import evidence


def test_location_directness_prefers_front_view():
    front = evidence("front", "不带前面板的 CPU 1517-3 PN/DP 前视图，PROFINET IO 接口 (X1)，标号⑦", page=2476)
    front.metadata["location_marker"] = "⑦"
    block = evidence("block", "CPU 1517-3 PN/DP X1 方框图和端口结构", page=2481)
    query = "CPU 1517-3 PN 的 X1 接口在哪里？"
    assert location_directness_score(query, front) > location_directness_score(query, block)
