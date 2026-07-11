import json

from safeplc_assist_box.schemas import AgentEvidence
from safeplc_assist_box.tools.chroma_figure_retriever import FigureMetadataMapper


def test_visual_status_image_available(tmp_path):
    image = tmp_path / "figure.png"
    image.write_bytes(b"image")
    cards = tmp_path / "cards.jsonl"
    cards.write_text(json.dumps({"figure_id": "fig1", "image_path": str(image)}) + "\n", encoding="utf-8")
    evidence = AgentEvidence("ev", "src", "manual", "figure", "", figure_id="fig1")
    enriched = FigureMetadataMapper(str(cards)).enrich(evidence)
    assert enriched.image_exists is True
    assert enriched.resolved_image_path == str(image)
    assert enriched.visual_evidence_status == "image_available"
