from conftest import run_sample


def test_location_query_does_not_add_port_subtask():
    response = run_sample("CPU 1517-3 PN 的 X1 接口在哪里？")
    ids = [item.subquestion_id for item in response.query_context.subquestions]
    assert ids == ["sq_x1_location"]
    assert response.selected_agents == ["Figure Agent"]
