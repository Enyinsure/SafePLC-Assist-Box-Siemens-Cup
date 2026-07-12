from retrieval_test_support import evidence
from wiring_test_support import run_wiring


def test_wiring_does_not_generalize_specific_module_rules():
    item = evidence("tm", "TM NPU 的前连接器接线必须检查端子极性。", model="TM NPU")
    result, _ = run_wiring([item])
    assert result.status == "NEED_CLARIFICATION"
    assert "具体模块和前连接器" in result.answer_fragment
