from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_streamlit_entrypoint_renders_without_exception() -> None:
    app = AppTest.from_file(PROJECT_ROOT / "app.py", default_timeout=20).run()

    assert not app.exception
    assert any(button.label == "开始智能查证" for button in app.button)
    assert any(area.label == "查证问题" for area in app.text_area)
