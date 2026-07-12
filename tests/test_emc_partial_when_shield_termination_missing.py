from conftest import run_sample


def test_emc_partial_when_shield_termination_missing():
    response = run_sample("EMC 安装时接地和屏蔽需要注意什么？")
    assert response.verdict == "PARTIAL"
    assert response.confidence == "MEDIUM"
    assert "接地控制柜或控制箱" in response.final_answer
    assert "噪声滤波器" in response.final_answer
    assert "屏蔽层连接方法或端接方法" in response.final_answer
    assert all(term not in response.final_answer for term in ("低阻抗接地", "屏蔽层两端接地", "动力线与信号线分离"))
