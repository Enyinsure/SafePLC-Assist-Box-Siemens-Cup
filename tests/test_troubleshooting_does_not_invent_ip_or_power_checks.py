from conftest import run_sample


def test_troubleshooting_does_not_invent_ip_or_power_checks():
    answer = run_sample("CPU 1517-3 PN 通信不上且指示灯异常，应先检查哪些信息？").final_answer
    assert all(term not in answer for term in ["IP 地址", "设备名", "供电状态", "最近修改", "诊断缓冲区"])
