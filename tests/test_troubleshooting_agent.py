from conftest import run_sample


def test_troubleshooting_agent_uses_led_evidence():
    response = run_sample("CPU 1517-3 PN 通信不上且指示灯异常，应先检查哪些信息？")
    assert "Troubleshooting Agent" in response.agent_plan.selected_agents
    assert all(term in response.final_answer for term in ["RUN/STOP", "ERROR", "MAINT", "X1 P1", "X1 P2", "LINK RX/TX"])
    assert all(term not in response.final_answer for term in ["IP 地址", "设备名", "供电状态", "最近修改"])


