from safeplc_assist_box.tools.metadata_normalizer import normalize_metadata


def test_synthetic_figure_id_not_manual_figure_number():
    item = normalize_metadata(
        text="端子分配视觉记录", metadata={"figure_id": "page_2478_visual", "page": 2478}, backend="chroma_figure"
    )
    assert item.visual_record_id == "page_2478_visual"
    assert item.manual_figure_number == ""
    assert item.metadata["figure_id_type"] == "synthetic_visual_id"
