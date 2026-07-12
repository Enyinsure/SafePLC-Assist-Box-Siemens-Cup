from conftest import run_sample
from test_compound_agent_queries import QUERY


def test_compound_led_claim_is_accepted():
    response = run_sample(QUERY)
    led_claim = next(
        claim for result in response.agent_results for claim in result.claims
        if claim.metadata.get("fact_type") == "led_checklist"
    )
    assert led_claim.metadata["structured_led_support"] is True
    assert response.verdict == "PASS"
    assert all("led" not in item.lower() for item in response.unsupported_claims)
