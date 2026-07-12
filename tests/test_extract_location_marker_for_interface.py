from safeplc_assist_box.tools.metadata_normalizer import extract_location_marker, extract_location_markers


PAGE_TEXT = """① 模式选择器
② 无功能
③ PROFIBUS 接口（X3）
④ 显示屏
⑤ 电源连接
⑥ PROFINET IO 接口 (X2)，带 1 个端口
⑦ PROFINET IO 接口（X1），带 2 个端口"""


def test_extract_location_marker_for_interface():
    assert extract_location_markers(PAGE_TEXT) == {"X3": "③", "X2": "⑥", "X1": "⑦"}
    assert extract_location_marker(PAGE_TEXT, "X1") == "⑦"
    assert extract_location_marker(PAGE_TEXT, "X2") == "⑥"
