from __future__ import annotations

import json
from pathlib import Path

from safeplc_assist_box.frontend.result_normalizer import normalize_response
from safeplc_assist_box.frontend.work_orders import (
    build_editable_work_order,
    work_order_to_json,
    work_order_to_markdown,
    work_order_to_text,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_work_order_exports_keep_evidence_references() -> None:
    payload = json.loads((PROJECT_ROOT / "reports" / "sample_acceptance_x1.json").read_text(encoding="utf-8"))
    result = normalize_response(payload)

    work_order = build_editable_work_order(result)
    json_text = work_order_to_json(work_order)
    markdown = work_order_to_markdown(work_order)
    text = work_order_to_text(work_order)

    assert work_order["device_model"] == "CPU 1517-3 PN/DP"
    assert any("E1" in source for source in work_order["evidence_sources"])
    assert "E1" in json_text
    assert "E1" in markdown
    assert "E1" in text
    assert work_order["status"] == "待人工复核"
    assert work_order["safety_notes"] == []
