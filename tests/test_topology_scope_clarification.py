from conftest import run_sample


def test_generic_hmi_interface_query_needs_clarification():
    response = run_sample("HMI 通过 PROFINET 与 CPU 连接时应使用哪个接口？")
    assert response.verdict == "NEED_CLARIFICATION"
    assert "标准 S7-1500" in response.final_answer and "S7-1500R/H" in response.final_answer


def test_rh_scoped_hmi_query_can_pass():
    response = run_sample("在 S7-1500R/H 示例中，HMI 应连接 CPU 哪个接口？")
    assert response.verdict == "PASS"
    assert response.evidence_pool.evidences[0].page == 1531
    assert "HMI 侧使用 PROFINET X1" in response.final_answer
    assert "CPU 侧使用 PROFINET X2" in response.final_answer
    claim = response.agent_results[0].claims[0]
    assert claim.model_scope == "S7-1500R/H"
    assert claim.metadata["scope_limited"] is True
