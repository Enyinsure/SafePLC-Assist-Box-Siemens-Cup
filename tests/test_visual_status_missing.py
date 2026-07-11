from safeplc_assist_box.schemas import AgentEvidence
from safeplc_assist_box.tools.chroma_figure_retriever import FigureMetadataMapper


def test_visual_status_missing_without_image_page_or_figure():
    evidence = AgentEvidence("ev", "src", "manual", "figure", "generic interface text")
    enriched = FigureMetadataMapper().enrich(evidence)
    assert enriched.image_exists is False
    assert enriched.visual_evidence_status == "missing"
