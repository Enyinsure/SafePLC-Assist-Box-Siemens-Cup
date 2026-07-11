from safeplc_assist_box.schemas import AgentEvidence
from safeplc_assist_box.tools.chroma_figure_retriever import FigureMetadataMapper


def test_visual_status_page_text_only():
    evidence = AgentEvidence(
        "ev", "src", "manual", "figure", "Figure 2-237 front view", page=2476, figure_number="Figure 2-237"
    )
    enriched = FigureMetadataMapper().enrich(evidence)
    assert enriched.image_exists is False
    assert enriched.visual_evidence_status == "page_text_only"
