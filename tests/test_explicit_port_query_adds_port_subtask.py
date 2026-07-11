from conftest import run_sample


def test_explicit_port_query_adds_port_subtask():
    response = run_sample("CPU 1517-3 PN 的 X1 有几个端口？端口名称是什么？")
    ids = [item.subquestion_id for item in response.query_context.subquestions]
    assert "sq_x1_ports" in ids
    assert "sq_x1_location" not in ids
