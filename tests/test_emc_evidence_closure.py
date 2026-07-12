from conftest import run_sample


def test_emc_page_6495_is_partial_and_evidence_closed():
    response = run_sample("EMC 安装时接地和屏蔽需要注意什么？")
    assert response.selected_agents == ["EMC Agent"]
    assert response.verdict == "PARTIAL" and response.confidence == "MEDIUM"
    assert response.evidence_pool.evidences[0].page == 6495
    assert "接地控制柜或控制箱" in response.final_answer
    assert "噪声滤波器" in response.final_answer
    assert "屏蔽层连接或端接方法" in response.final_answer
    assert all(term not in response.final_answer for term in ["低阻抗接地", "屏蔽层两端接地", "分离敷设"])
