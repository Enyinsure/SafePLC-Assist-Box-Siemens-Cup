from safeplc_assist_box.tools.metadata_normalizer import normalize_metadata


def test_model_inferred_from_text_chroma_section():
    item = normalize_metadata(
        text="操作和显示元件", metadata={"section": "CPU 1517-3 PN/DP 不带前面板的模块前视图"},
        backend="chroma_text", query_text="CPU 1517-3 PN 的 X1 在哪里？",
    )
    assert item.module_model == "CPU 1517-3 PN/DP"
    assert item.module == "CPU 1517-3 PN/DP"
    assert item.device_family == "S7-1500"
    assert item.metadata["model_inferred_from_text"] is True
