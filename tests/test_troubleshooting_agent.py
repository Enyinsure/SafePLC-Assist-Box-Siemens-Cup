from conftest import run_sample


def test_troubleshooting_agent_distinguishes_manual_confirmation():
    response = run_sample("CPU 1517-3 PN 通信不上且指示灯异常，应先检查哪些信息？")
    assert "Troubleshooting Agent" in response.agent_plan.selected_agents
    assert "人工确认" in response.final_answer or "人工复核" in response.final_answer


