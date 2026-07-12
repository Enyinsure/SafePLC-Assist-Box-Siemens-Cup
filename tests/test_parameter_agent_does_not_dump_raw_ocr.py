from conftest import run_sample


def test_parameter_agent_does_not_dump_raw_ocr():
    response = run_sample("PS 60W 24/48/60VDC HF 的电源电压允许范围是多少？")
    claim = response.agent_results[0].claims[0]
    assert len(claim.claim_text) < 180
    assert "rated inputs are" not in claim.claim_text
    assert claim.metadata["inference_level"] == "direct"
