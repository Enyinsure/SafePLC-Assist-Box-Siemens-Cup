from safeplc_assist_box.schemas import AgentResult, AgentStatus, QueryContext, SlotResult


def test_schemas_serialize_to_dict():
    ctx = QueryContext(original_query="q", slots={"module_model": SlotResult("module_model", "CPU")})
    data = ctx.to_dict()
    assert data["slots"]["module_model"]["value"] == "CPU"
    result = AgentResult("Parameter Agent", "t1", AgentStatus.ABSTAIN.value)
    assert result.to_dict()["status"] == "ABSTAIN"

