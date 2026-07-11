from conftest import run_sample


def test_compound_hmi_query_decomposition():
    response = run_sample("CPU 1517-3 PN 的 X1 接口在哪里，并说明 PROFINET 与 HMI 连接时的注意事项。")
    ids = [item.subquestion_id for item in response.query_context.subquestions]
    assert ids == ["sq_x1_location", "sq_profinet_hmi", "sq_network_notes"]
    assert "sq_x1_ports" not in ids
