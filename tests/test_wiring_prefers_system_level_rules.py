from retrieval_test_support import evidence
from wiring_test_support import run_wiring


def test_wiring_prefers_system_level_rules():
    module = evidence("module", "TM NPU 接线时应检查端子极性。", model="TM NPU", score=0.95)
    system = evidence(
        "system",
        "端子接线应使用 SELV/PELV 电源并连接保护性导线。",
        model="S7-1500 / ET 200MP",
        score=0.3,
        manual_title="S7-1500 ET 200MP 系统手册",
    )
    result, _ = run_wiring([module, system])
    assert result.status == "ANSWERED"
    assert result.evidence_ids == ["system"]
    assert "SELV/PELV" in result.answer_fragment
