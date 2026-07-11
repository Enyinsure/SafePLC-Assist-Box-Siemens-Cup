from conftest import run_sample


def test_parameter_agent_answers_with_table_evidence():
    response = run_sample("PS 60W 24/48/60VDC HF 的电源电压允许范围是多少？")
    assert "Parameter Agent" in response.agent_plan.selected_agents
    assert any(r.agent_name == "Parameter Agent" and r.evidence_ids for r in response.agent_results)
    assert response.judge_decision.verdict == "PASS"


