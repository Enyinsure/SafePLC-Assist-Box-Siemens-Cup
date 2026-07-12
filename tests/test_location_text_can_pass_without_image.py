from safeplc_assist_box.agents.judge_agent import JudgeAgent
from safeplc_assist_box.schemas import AgentClaim, AgentResult, EvidencePool, QueryContext
from retrieval_test_support import evidence


def test_location_text_can_pass_without_image():
    item = evidence("ev1", "CPU 1517-3 PN/DP 前视图标号⑦为 PROFINET IO 接口 X1", page=2476, manual_figure_number="图 2-237")
    item.visual_evidence_status = "page_text_only"
    claim = AgentClaim("c1", "CPU 1517-3 PN/DP 前视图标号⑦为 PROFINET IO 接口 X1", "location", ["ev1"], model_scope="CPU 1517-3 PN/DP", direct_support=True)
    result = AgentResult("Figure Agent", "t1", "ANSWERED", claims=[claim], evidence_ids=["ev1"])
    context = QueryContext("CPU 1517-3 PN 的 X1 在哪里？", question_type="FIGURE", required_modalities=["figure"])
    decision = JudgeAgent().decide(context, [result], EvidencePool(evidences=[item]))
    assert decision.verdict == "PASS"
    assert decision.confidence == "MEDIUM"
