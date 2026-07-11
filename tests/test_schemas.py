from safeplc_assist_box.schemas import AgentResult, AgentStatus, QueryContext, SafePLCResponse, SlotResult


def test_schemas_serialize_to_dict():
    ctx = QueryContext(original_query="q", slots={"module_model": SlotResult("module_model", "CPU")})
    data = ctx.to_dict()
    assert data["slots"]["module_model"]["value"] == "CPU"
    result = AgentResult("Parameter Agent", "t1", AgentStatus.ABSTAIN.value)
    assert result.to_dict()["status"] == "ABSTAIN"


def test_response_flattened_fields_are_json_serializable():
    response = SafePLCResponse(
        query="q",
        context="",
        mode="SAMPLE",
        query_context=QueryContext(original_query="q"),
        agent_plan=None,
        agent_results=[],
        evidence_pool=None,
        judge_decision=None,
        verifier={},
        final_answer="answer",
        question_type="PARAMETER",
        selected_agents=["Parameter Agent"],
        verdict="PASS",
        total_tool_calls=1,
        generated_at="2026-07-11 00:00:00",
    )
    data = response.to_dict()
    assert data["question_type"] == "PARAMETER"
    assert data["selected_agents"] == ["Parameter Agent"]
    assert data["total_tool_calls"] == 1
