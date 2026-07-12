from test_judge_accepts_structured_emc_facts_from_english_evidence import structured_emc_decision


def test_emc_coverage_note_is_not_fact_claim():
    result, decision = structured_emc_decision()
    claim = result.claims[0]
    assert "未直接覆盖" not in claim.claim_text
    assert claim.metadata["coverage_note"]
    assert claim.metadata["missing_topics"] == ["屏蔽层连接方法", "屏蔽层端接方法"]
    assert all("未直接覆盖" not in item for item in decision.supported_claims)
