#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import importlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from datetime import datetime


ROOT = Path(os.environ.get("SAFEPLC_PROJECT_ROOT", Path(__file__).resolve().parents[1])).resolve()
ASSIST_DIR = ROOT / "safeplc_assist_box"

# 确保从 safeplc_assist_box 目录导入本地 V1.1 模块
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ASSIST_DIR) not in sys.path:
    sys.path.insert(0, str(ASSIST_DIR))


def check_path(path: Path, kind: str = "file") -> dict:
    exists = path.exists()
    ok = exists and (path.is_file() if kind == "file" else path.is_dir())
    return {
        "path": str(path),
        "kind": kind,
        "ok": bool(ok),
    }


def check_json(path: Path) -> dict:
    result = check_path(path, "file")

    if not result["ok"]:
        result["readable_json"] = False
        return result

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        result["readable_json"] = True
        result["items"] = len(data) if isinstance(data, list) else None
    except Exception as e:
        result["readable_json"] = False
        result["error"] = str(e)

    return result


def check_import(module_path: Path) -> dict:
    result = check_path(module_path, "file")

    if not result["ok"]:
        result["importable"] = False
        return result

    try:
        module_name = module_path.stem
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        mod = importlib.util.module_from_spec(spec)
        assert spec and spec.loader

        # dataclass 在动态导入时需要模块先进入 sys.modules
        sys.modules[module_name] = mod

        spec.loader.exec_module(mod)
        result["importable"] = True
    except Exception as e:
        result["importable"] = False
        result["error"] = str(e)

    return result


def check_module_import(module_name: str) -> dict:
    try:
        importlib.import_module(module_name)
        return {
            "module": module_name,
            "kind": "module",
            "ok": True,
            "importable": True,
        }
    except Exception as e:
        return {
            "module": module_name,
            "kind": "module",
            "ok": False,
            "importable": False,
            "error": str(e),
        }


def main() -> int:
    checks = {
        "project": "SafePLC-Assist Box",
        "version": "V1.1",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "root": str(ROOT),

        "paths": [
            check_path(ROOT, "dir"),
            check_path(ASSIST_DIR, "dir"),
            check_path(ASSIST_DIR / "app_assist_box.py", "file"),
            check_path(ROOT / "run_streamlit_safeplc_assist_box.sh", "file"),
            check_path(ASSIST_DIR / "schemas.py", "file"),
            check_path(ASSIST_DIR / "agents" / "orchestrator.py", "file"),
            check_path(ASSIST_DIR / "agents" / "supervisor_agent.py", "file"),
            check_path(ASSIST_DIR / "evidence" / "evidence_pool.py", "file"),
        ],

        "json_files": [
            check_json(ASSIST_DIR / "demo_cases.json"),
            check_json(ASSIST_DIR / "testset_v11_basic.json"),
            check_json(ASSIST_DIR / "eval_report_v11.json"),
        ],

        "imports": [
            check_import(ASSIST_DIR / "safety_risk_guard_v11.py"),
            check_import(ASSIST_DIR / "question_classifier_v11.py"),
            check_import(ASSIST_DIR / "evidence_confidence_v11.py"),
            check_import(ASSIST_DIR / "answer_evidence_checker_v11.py"),
            check_module_import("safeplc_assist_box.agents.orchestrator"),
            check_module_import("safeplc_assist_box.agents.judge_agent"),
        ],
    }

    all_ok = True

    for item in checks["paths"]:
        all_ok = all_ok and bool(item.get("ok"))

    for item in checks["json_files"]:
        all_ok = all_ok and bool(item.get("ok")) and bool(item.get("readable_json"))

    for item in checks["imports"]:
        all_ok = all_ok and bool(item.get("ok")) and bool(item.get("importable"))

    checks["overall_ok"] = all_ok

    report_path = ASSIST_DIR / "self_check_report_v11.json"
    report_path.write_text(
        json.dumps(checks, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("SafePLC-Assist Box V1.1 Self Check")
    print("=" * 50)
    print("Root:", ROOT)
    print("Assist dir:", ASSIST_DIR)
    print("Overall OK:", all_ok)
    print("Report saved to:", report_path)

    if not all_ok:
        print()
        print("Failed items:")

        for group in ["paths", "json_files", "imports"]:
            for item in checks[group]:
                bad = False

                if not item.get("ok", True):
                    bad = True

                if "readable_json" in item and not item["readable_json"]:
                    bad = True

                if "importable" in item and not item["importable"]:
                    bad = True

                if bad:
                    print("-", group, item)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
