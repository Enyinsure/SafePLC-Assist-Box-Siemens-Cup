from test_judge_accepts_structured_emc_facts_from_english_evidence import structured_emc_decision


def test_emc_canonical_chinese_facts_match_english_evidence():
    result, _ = structured_emc_decision()
    metadata = result.claims[0].metadata
    assert metadata["positive_facts"] == [
        "可采用接地控制柜或控制箱。",
        "可在电源线上使用噪声滤波器。",
        "该系统适用于工业环境。",
    ]
    assert metadata["evidence_positive_facts"] == metadata["positive_facts"]
