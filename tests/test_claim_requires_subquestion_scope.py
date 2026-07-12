from safeplc_assist_box.agents.judge_agent import JudgeAgent
from safeplc_assist_box.schemas import AgentClaim, AgentResult, EvidencePool, QueryContext, SubQuestion
from retrieval_test_support import evidence


def test_claim_requires_subquestion_scope():
    item = evidence("ev", "direct X1 evidence")
    claim = AgentClaim("c", "direct X1 evidence", "location", ["ev"], direct_support=True)
    context = QueryContext("CPU 1517-3 PN X1 在哪里？", subquestions=[SubQuestion("sq", "X1 location", "locate")])
    decision = JudgeAgent().decide(context, [AgentResult("Figure Agent", "t", "ANSWERED", claims=[claim], evidence_ids=["ev"])], EvidencePool([item]))
    assert any("missing_subquestion_scope" in item for item in decision.unsupported_claims)
