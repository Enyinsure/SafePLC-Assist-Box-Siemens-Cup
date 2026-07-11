import json

from safeplc_assist_box.schemas import AgentEvidence
from safeplc_assist_box.tools.chroma_figure_retriever import FigureMetadataMapper


def test_relative_image_resolution_uses_visual_dir_then_cards_dir(tmp_path):
    visual = tmp_path / "visual"
    visual.mkdir()
    image = visual / "page.png"
    image.write_bytes(b"image")
    cards = tmp_path / "cards.jsonl"
    cards.write_text(json.dumps({"figure_id": "fig1", "image_path": "page.png"}) + "\n", encoding="utf-8")
    enriched = FigureMetadataMapper(str(cards), str(visual)).enrich(
        AgentEvidence("ev", "src", "manual", "figure", "", figure_id="fig1")
    )
    assert enriched.raw_image_path == "page.png"
    assert enriched.resolved_image_path == str(image)
    assert enriched.image_exists is True
