import json

from safeplc_assist_box.tools.chroma_figure_retriever import FigureMetadataMapper


def test_figure_metadata_mapping_counts_cards(tmp_path):
    cards = tmp_path / "cards.jsonl"
    cards.write_text(json.dumps({"figure_id": "f1", "figure_number": "Figure 2-237", "page": 2476}) + "\n", encoding="utf-8")
    mapper = FigureMetadataMapper(str(cards), str(tmp_path))
    assert mapper.card_count() == 1
