from conftest import run_sample


def test_topology_agent_selected_for_profinet_hmi():
    response = run_sample("HMI 通过 PROFINET 与 CPU 连接时应使用哪个接口？")
    assert "Topology Agent" in response.agent_plan.selected_agents
    assert any("PROFINET" in ev.text for ev in response.evidence_pool.evidences)


