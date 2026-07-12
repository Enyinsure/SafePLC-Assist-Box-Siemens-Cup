from test_judge_accepts_structured_emc_facts_from_english_evidence import structured_emc_decision


def test_emc_partial_preserves_coverage_note():
    _, decision = structured_emc_decision()
    assert decision.verdict == "PARTIAL"
    assert "【待确认】当前证据未直接覆盖屏蔽层连接或端接方法" in decision.final_answer
    assert "需继续查对应安装章节" in decision.final_answer
