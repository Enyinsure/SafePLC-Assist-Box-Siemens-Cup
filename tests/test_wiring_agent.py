from conftest import run_sample


def test_wiring_agent_provides_safety_note():
    response = run_sample("S7-1500 端子接线注意事项是什么？")
    assert "Wiring Agent" in response.agent_plan.selected_agents
    assert "具备资质" in response.final_answer


