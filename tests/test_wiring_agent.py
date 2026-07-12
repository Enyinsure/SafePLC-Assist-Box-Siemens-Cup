from conftest import run_sample


def test_wiring_agent_provides_evidenced_requirements():
    response = run_sample("S7-1500 端子接线注意事项是什么？")
    assert "Wiring Agent" in response.agent_plan.selected_agents
    assert "SELV/PELV" in response.final_answer
    assert "保护性导线" in response.final_answer
    assert "具备资质" not in response.final_answer


