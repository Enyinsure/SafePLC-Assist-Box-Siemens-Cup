from safeplc_assist_box.agents.context_analyzer import ContextAnalyzer


def test_context_analyzer_extracts_slots_and_missing_model():
    ctx = ContextAnalyzer().analyze("某个模块的电源电压允许范围是多少？")
    assert ctx.question_type == "PARAMETER"
    assert "module_model" in ctx.missing_slots
    assert ctx.clarify_question

