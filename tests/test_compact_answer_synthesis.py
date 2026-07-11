from safeplc_assist_box.agents.evidence_closed_synthesizer import EvidenceClosedSynthesizer
from safeplc_assist_box.schemas import AgentClaim, AgentEvidence, QueryContext


def test_compact_answer_synthesis_for_x1():
    ev = AgentEvidence("ev1", "manual", "manual", "figure", "X1 P1 X1 P2", page=2476, figure_number="Figure 2-237")
    claim = AgentClaim("c1", "X1 has two ports", "location", ["ev1"], model_scope="CPU 1517-3 PN/DP", metadata={"page": 2476, "figure_number": "Figure 2-237", "ports": ["X1 P1", "X1 P2"]})
    answer = EvidenceClosedSynthesizer().synthesize(QueryContext("q"), [claim], {"ev1": ev}, "PASS")
    assert "2476" in answer
    assert "Figure 2-237" in answer
    assert len(answer) < 500
