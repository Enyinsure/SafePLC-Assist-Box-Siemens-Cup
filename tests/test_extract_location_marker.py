from safeplc_assist_box.tools.metadata_normalizer import extract_location_marker


def test_extract_location_marker():
    assert extract_location_marker("⑦ PROFINET IO 接口 (X1)，带 2 个端口", "X1") == "⑦"
    assert extract_location_marker("⑦ PROFINET IO 接口 (X1)，带 2 个端口") == ""
    assert extract_location_marker("X1 interface") == ""
