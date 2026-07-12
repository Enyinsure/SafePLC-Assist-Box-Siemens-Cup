from safeplc_assist_box.tools.metadata_normalizer import normalize_metadata


def test_order_number_inferred_from_manual_text():
    item = normalize_metadata(
        text="CPU 1517-3 PN/DP 订货号 6ES7517-3AP00-0AB0", metadata={}, backend="chroma_text",
        query_text="CPU 1517-3 PN 的 X1 在哪里？",
    )
    assert item.order_number == "6ES7517-3AP00-0AB0"
    assert item.metadata["order_number_inferred_from_text"] is True
