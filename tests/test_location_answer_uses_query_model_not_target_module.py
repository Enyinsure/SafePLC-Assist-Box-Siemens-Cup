from safeplc_assist_box.agents.evidence_closed_synthesizer import EvidenceClosedSynthesizer
from safeplc_assist_box.schemas import AgentClaim, AgentEvidence, QueryContext


def test_location_answer_uses_query_model_not_target_module():
    item = AgentEvidence("ev1", "manual", "manual", "text", "X1 front view", page=10)
    claim = AgentClaim("c1", "X1 location", "location", ["ev1"], metadata={"interface_name": "X1", "page": 10})
    answer = EvidenceClosedSynthesizer().synthesize(
        QueryContext("CPU 1517-3 PN 的 X1 在哪里？"), [claim], {"ev1": item}, "PASS"
    )
    assert answer.startswith("【结论】CPU 1517-3 PN/DP 的 X1")
    assert "Target module" not in answer
    assert "目标模块" not in answer
