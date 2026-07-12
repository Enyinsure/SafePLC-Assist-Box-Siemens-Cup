from conftest import run_sample


def test_parameter_agent_page_6313():
    response = run_sample("PS 60W 24/48/60VDC HF 的电源电压允许范围是多少？")
    assert response.verdict == "PASS"
    assert response.evidence_pool.evidences[0].page == 6313
    assert "静态 19.2～72 V DC" in response.final_answer
    assert "动态 18.5～75.5 V DC" in response.final_answer
