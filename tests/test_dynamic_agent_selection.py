from conftest import run_sample


def test_dynamic_selection_uses_multiple_agents_for_multimodal_query():
    response = run_sample("CPU 1517-3 PN 的 X1 接口在哪里，并说明 PROFINET 与 HMI 连接时的注意事项。")
    selected = set(response.agent_plan.selected_agents)
    assert "Figure Agent" in selected
    assert "Topology Agent" in selected
    assert len(selected) <= 4


