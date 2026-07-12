from emc_test_support import run_emc
from retrieval_test_support import evidence


def test_emc_prefers_two_or_more_installation_facts():
    one = evidence("one", "Industrial environment", score=0.95)
    two = evidence("two", "grounded control cabinets/control boxes and noise filters in the supply lines", score=0.3)
    result, _ = run_emc([one, two])
    assert result.status == "PARTIAL"
    assert result.evidence_ids == ["two"]
    assert result.claims[0].metadata["installation_fact_count"] == 2
