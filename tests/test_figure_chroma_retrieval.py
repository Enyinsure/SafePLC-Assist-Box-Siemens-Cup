import json

from safeplc_assist_box.schemas import AgentEvidence
from safeplc_assist_box.tools.chroma_figure_retriever import FigureMetadataMapper


def test_figure_chroma_metadata_enrichment_from_cards(tmp_path):
    card = tmp_path / "cards.jsonl"
    image = tmp_path / "page.png"
    image.write_bytes(b"fake")
    card.write_text(
        json.dumps({"figure_id": "fig1", "figure_number": "Figure 2-237", "page": 2476, "image_path": str(image)}) + "\n",
        encoding="utf-8",
    )
    ev = AgentEvidence("", "src", "sample", "figure", "Figure 2-237 shows X1", figure_number="Figure 2-237")
    enriched = FigureMetadataMapper(str(card), str(tmp_path)).enrich(ev)
    assert enriched.page == 2476
    assert enriched.image_path == str(image)
    assert enriched.metadata["has_visual_evidence"] is True
