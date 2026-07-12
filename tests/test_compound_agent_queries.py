from safeplc_assist_box.agents.context_analyzer import ContextAnalyzer
from safeplc_assist_box.agents.query_decomposer import QueryDecomposer
from safeplc_assist_box.agents.supervisor_agent import SupervisorAgent
from conftest import run_sample


QUERY = "CPU 1517-3 PN 的 X1 在哪里、包含几个端口，并说明通信不上且指示灯异常时应先检查什么？"


def plan():
    context = ContextAnalyzer().analyze(QUERY)
    context.subquestions = QueryDecomposer().decompose(context)
    return context, SupervisorAgent().plan(context)


def test_compound_query_creates_diagnostic_subquestion():
    context, _ = plan()
    assert [item.subquestion_id for item in context.subquestions] == ["sq_x1_location", "sq_x1_ports", "sq_comm_led_diagnosis"]


def test_agent_task_uses_only_assigned_subquestions():
    _, result = plan()
    assert result.task_assignments["Figure Agent"].subquestion_ids == ["sq_x1_location", "sq_x1_ports"]
    assert result.task_assignments["Troubleshooting Agent"].subquestion_ids == ["sq_comm_led_diagnosis"]
    assert result.task_assignments["Figure Agent"].metadata["original_query"] == QUERY


def test_compound_query_does_not_select_parameter_agent():
    _, result = plan()
    assert result.selected_agents == ["Figure Agent", "Troubleshooting Agent"]
    assert "Parameter Agent" not in result.selected_agents


def test_figure_agent_query_excludes_fault_terms():
    _, result = plan()
    query = result.task_assignments["Figure Agent"].query
    assert "通信不上" not in query and "指示灯异常" not in query


def test_troubleshooting_query_excludes_location_request():
    _, result = plan()
    query = result.task_assignments["Troubleshooting Agent"].query
    assert "物理位置" not in query and "几个端口" not in query


def test_compound_location_keeps_page_2476_marker_7():
    response = run_sample(QUERY)
    location = next(item for item in response.evidence_pool.evidences if item.page == 2476)
    assert location.figure_number == "Figure 2-237"
    assert "⑦" in response.final_answer and "标号⑤" not in response.final_answer


def test_compound_diagnosis_uses_page_2482():
    response = run_sample(QUERY)
    assert any(item.page == 2482 and item.figure_number == "Figure 2-240" for item in response.evidence_pool.evidences)


def test_compound_answer_covers_all_three_subquestions():
    response = run_sample(QUERY)
    assert response.verdict in {"PASS", "PARTIAL"}
    assert all(item["answered"] for item in response.judge_decision.coverage.values())
    for term in ("X1 P1", "X1 P2", "RUN/STOP", "ERROR", "MAINT", "LINK RX/TX"):
        assert term in response.final_answer
    for term in ("Target module", "目标模块", "IP 地址", "设备名", "供电状态"):
        assert term not in response.final_answer
