from retrieval_test_support import evidence
from wiring_test_support import run_wiring


def test_wiring_does_not_generalize_rh_rules():
    item = evidence("rh", "S7-1500R/H 接线时应连接保护导线。", model="S7-1500R/H")
    result, _ = run_wiring([item])
    assert result.status == "NEED_CLARIFICATION"
    assert "模块型号或订货号" in result.answer_fragment
