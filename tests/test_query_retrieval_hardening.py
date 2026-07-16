from safeplc_assist_box.agents.context_analyzer import ContextAnalyzer
from safeplc_assist_box.agents.query_decomposer import QueryDecomposer
from safeplc_assist_box.evidence.fact_extractors import extract_emc_facts, extract_topology_fact
from safeplc_assist_box.tools.chroma_text_retriever import ChromaTextRetriever


def test_explicit_emc_beats_generic_profinet_topology_trigger():
    ctx = ContextAnalyzer().analyze(
        "PROFINET 铜缆与变频器动力电缆并行敷设时，应注意哪些 EMC、屏蔽和接地要求？"
    )
    assert ctx.question_type == "EMC"
    assert not ctx.missing_slots


def test_order_number_is_kept_as_exact_device_scope():
    ctx = ContextAnalyzer().analyze(
        "请核查 6ES7556-1AA00-0AB0 的供电要求，其他订货号不要作为最终依据。"
    )
    assert ctx.slots["order_number"].value == "6ES7556-1AA00-0AB0"
    assert ctx.slots["module_model"].value == "6ES7556-1AA00-0AB0"
    assert "module_model" not in ctx.missing_slots


def test_exact_page_figure_lookup_does_not_require_model_slots():
    ctx = ContextAnalyzer().analyze("请展示资料页 8078 对应的原始图示。")
    assert "module_model" not in ctx.missing_slots
    assert "interface_name" not in ctx.missing_slots


def test_system_level_wiring_question_can_retrieve_general_guidance():
    ctx = ContextAnalyzer().analyze("S7-1500 系统接线时，保护导线、SELV/PELV 和线缆布置有哪些要求？")
    assert ctx.question_type == "WIRING"
    assert not ctx.missing_slots


def test_work_order_routes_to_specialist_before_export():
    ctx = ContextAnalyzer().analyze(
        "一台 S7-1500 设备运行中偶发通信中断，请根据手册证据给出排查顺序并生成维护工单。"
    )
    subquestions = QueryDecomposer().decompose(ctx)
    assert subquestions
    assert subquestions[0].expected_agents == ["Troubleshooting Agent"]


def test_lexical_terms_cover_exact_mlfb_and_emc_topics():
    retriever = ChromaTextRetriever("")
    exact = retriever._lexical_terms("查询 6ES7556-1AA00-0AB0 的供电要求", exact_only=False)
    assert exact == ["6ES7556-1AA00-0AB0"]
    emc = retriever._lexical_terms("动力电缆并行敷设的 EMC 屏蔽接地要求", exact_only=False)
    assert "电磁兼容" in emc
    assert "屏蔽" in emc
    assert "接地" in emc


def test_broader_topology_fact_is_scoped_and_conservative():
    claim = extract_topology_fact(
        "S7-1500 CPU 通过 PROFINET 接入工业以太网交换机。具体接口取决于设备组态。"
    )
    assert "PROFINET" in claim
    assert "型号" in claim or "接口" in claim


def test_broader_emc_fact_extracts_normative_installation_sentence():
    facts = extract_emc_facts(
        "通信电缆与动力电缆应分开敷设，并确保屏蔽层按安装规范接地。"
    )
    assert facts
    assert any("屏蔽" in fact or "动力电缆" in fact for fact in facts)
