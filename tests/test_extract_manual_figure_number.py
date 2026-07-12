from safeplc_assist_box.tools.metadata_normalizer import extract_manual_figure, normalize_metadata


def test_extract_manual_figure_number_and_caption():
    text = "图 2-237 不带前面板的 CPU 1517-3 PN/DP 的前视图。"
    number, caption = extract_manual_figure(text)
    item = normalize_metadata(text=text, metadata={}, backend="chroma_text")
    assert number == "图 2-237"
    assert "前视图" in caption
    assert item.manual_figure_number == "图 2-237"
    assert "前视图" in item.manual_figure_caption
