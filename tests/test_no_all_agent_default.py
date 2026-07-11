from conftest import run_sample


def test_default_routing_does_not_call_all_agents():
    response = run_sample("PS 60W 24/48/60VDC HF 的电源电压允许范围是多少？")
    assert response.agent_plan.routing_strategy == "adaptive"
    assert len(response.agent_plan.selected_agents) < 8
    assert "all_agents" not in response.agent_plan.routing_strategy


