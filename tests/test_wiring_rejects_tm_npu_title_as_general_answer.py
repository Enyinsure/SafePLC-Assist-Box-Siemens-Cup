from retrieval_test_support import evidence
from wiring_test_support import run_wiring


def test_wiring_rejects_tm_npu_title_as_general_answer():
    item = evidence("tm-title", "接线\n端子分配\nTM NPU 底部的端子\n下图显示了 TM NPU 底部的端子：", model="TM NPU")
    result, _ = run_wiring([item])
    assert result.status == "ABSTAIN"
    assert "端子分配" not in result.answer_fragment
