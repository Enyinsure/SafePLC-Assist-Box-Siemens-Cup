from safeplc_assist_box.evidence.evidence_ranker import location_directness_score
from retrieval_test_support import evidence


def test_location_directness_penalizes_sync_domain():
    front = evidence("front", "CPU 1517-3 PN/DP 前视图，接口位置 X1，标号⑦", page=2476)
    sync = evidence("sync", "CPU 1517-3 PN/DP X1 发送周期、同步域、IRT 周期", page=8726)
    query = "CPU 1517-3 PN 的 X1 在哪里？"
    assert location_directness_score(query, front) > location_directness_score(query, sync) + 0.8
