from conftest import run_sample


def test_wiring_does_not_invent_qualified_personnel():
    response = run_sample("S7-1500 端子接线注意事项是什么？")
    assert "具备资质" not in response.agent_results[0].claims[0].claim_text
