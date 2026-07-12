from conftest import run_sample


def test_topology_agent_selected_for_profinet_hmi():
    response = run_sample("HMI 通过 PROFINET 与 CPU 连接时应使用哪个接口？")
    assert response.agent_plan.selected_agents == []
    assert response.verdict == "NEED_CLARIFICATION"
    assert "CPU 型号" in response.final_answer


