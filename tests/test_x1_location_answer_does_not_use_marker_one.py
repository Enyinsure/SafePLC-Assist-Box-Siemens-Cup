from safeplc_assist_box.agents.evidence_closed_synthesizer import EvidenceClosedSynthesizer
from safeplc_assist_box.schemas import AgentClaim, QueryContext
from safeplc_assist_box.tools.metadata_normalizer import normalize_metadata
from test_extract_location_marker_for_interface import PAGE_TEXT


def test_x1_location_answer_does_not_use_marker_one():
    item = normalize_metadata(
        text=PAGE_TEXT + "\n图 2-237 CPU 1517-3 PN/DP 的前视图",
        metadata={"page_no": 10}, backend="chroma_text", query_text="CPU 1517-3 PN 的 X1 在哪里？",
    )
    claim = AgentClaim(
        "c1", "CPU 1517-3 PN/DP X1 location", "location", [item.evidence_id],
        metadata={"interface_name": "X1", "location_marker": item.metadata["location_marker"], "page": 10},
    )
    answer = EvidenceClosedSynthesizer().synthesize(
        QueryContext("CPU 1517-3 PN 的 X1 在哪里？"), [claim], {item.evidence_id: item}, "PASS"
    )
    assert "⑦" in answer
    assert "①" not in answer
