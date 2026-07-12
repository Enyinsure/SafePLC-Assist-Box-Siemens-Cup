from safeplc_assist_box.tools.metadata_normalizer import extract_location_marker, normalize_metadata
from test_extract_location_marker_for_interface import PAGE_TEXT


def test_location_marker_skips_unrelated_first_marker():
    item = normalize_metadata(
        text=PAGE_TEXT,
        metadata={"page_no": 10},
        backend="chroma_text",
        query_text="CPU 1517-3 PN 的 X1 在哪里？",
    )
    assert extract_location_marker(PAGE_TEXT, "X1") != "①"
    assert item.metadata["location_marker"] == "⑦"
    assert item.metadata["location_marker_interface"] == "X1"
    assert item.metadata["location_markers"]["X2"] == "⑥"
