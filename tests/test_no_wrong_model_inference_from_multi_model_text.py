from safeplc_assist_box.tools.metadata_normalizer import normalize_metadata


MULTI_MODEL_TEXT = "CPU 1518-4 PN/DP 与 CPU 1517-3 PN/DP 的接口说明。"


def test_query_model_selected_from_multi_model_text():
    item = normalize_metadata(
        text=MULTI_MODEL_TEXT, metadata={}, backend="chroma_text",
        query_text="CPU 1517-3 PN 的 X1 在哪里？",
    )
    assert item.module_model == "CPU 1517-3 PN/DP"


def test_multi_model_text_without_query_target_remains_empty():
    item = normalize_metadata(text=MULTI_MODEL_TEXT, metadata={}, backend="chroma_text", query_text="X1 在哪里？")
    assert item.module_model == ""


def test_single_order_number_is_not_attached_to_ambiguous_multi_model_text():
    item = normalize_metadata(
        text=MULTI_MODEL_TEXT + " 6ES7518-4AP00-0AB0", metadata={}, backend="chroma_text",
        query_text="CPU 1517-3 PN 的 X1 在哪里？",
    )
    assert item.module_model == "CPU 1517-3 PN/DP"
    assert item.order_number == ""
