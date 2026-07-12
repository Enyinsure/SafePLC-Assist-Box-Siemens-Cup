from conftest import run_sample


def test_wiring_claim_terms_exist_in_evidence():
    response = run_sample("S7-1500 端子接线注意事项是什么？")
    claim = response.agent_results[0].claims[0]
    evidence = response.evidence_pool.evidences[0].text
    for term in ("电源隔离设备", "SELV/PELV", "保护性导线"):
        assert term in claim.claim_text and term in evidence
