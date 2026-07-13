from __future__ import annotations

import copy
from functools import lru_cache

from benchmark.generation.build_full_360 import build_full_360
from benchmark.generation.common import CORE_CASES_PATH, load_jsonl, sha256_file


def make_seed(index: int) -> dict:
    model = f"CPU 1517-3 PN/DP TEST {index:03d}"
    order_number = f"6ES7{500 + index:03d}-0AA00-0AB0"
    page = 7000 + index
    return {
        "seed_id": f"seed_test_{index:04d}",
        "source_type": "text_chroma",
        "manual_title": "SIMATIC S7-1500 test manual fixture",
        "device_family": "S7-1500",
        "module_model": model,
        "order_number": order_number,
        "page": page,
        "section": f"Verified fixture section {index:03d}",
        "figure_id": f"图 T-{index:03d}",
        "modality": ["text"],
        "evidence_excerpt": (
            f"{model} {order_number} 电源电压额定值 24 V。静态范围 19.2 V 至 72 V，"
            f"动态范围 18.5 V 至 75.5 V。① PROFINET IO 接口 X1，带 2 个端口。"
            "X1 LINK 绿色表示链路已建立。保护导线必须可靠连接。屏蔽层应大面积接地。"
        ),
        "structured_facts": {
            "parameter": {
                "rated_values": [24.0],
                "static_lower": 19.2,
                "static_upper": 72.0,
                "dynamic_lower": 18.5,
                "dynamic_upper": 75.5,
                "complete": True,
            },
            "interfaces": ["X1", "X2"],
            "ports": [{"interface": "X1", "port_count": 2}],
            "figure": {"number": f"图 T-{index:03d}", "caption": f"{model} 前视图"},
            "location_markers": {"X1": "①"},
            "led_checks": {"X1": ["LINK 绿色：链路已建立"]},
            "wiring_requirements": ["保护导线必须可靠连接。"],
            "emc_measures": ["屏蔽层应大面积接地。"],
            "topology": "HMI PROFINET X1 与 CPU PROFINET X2 连接。",
        },
        "source_record_id": f"record-{index:04d}",
        "source_verified": True,
        "source_path_env": "SAFEPLC_CHROMA_DIR",
        "collection_name": "fixture_collection",
    }


@lru_cache(maxsize=1)
def _cached_dataset() -> dict:
    seeds = [make_seed(index) for index in range(1, 101)]
    core = load_jsonl(CORE_CASES_PATH)
    built = build_full_360(seeds, core, core_sha256=sha256_file(CORE_CASES_PATH))
    return {**built, "seeds": seeds, "core": core}


def build_fixture_dataset() -> dict:
    return copy.deepcopy(_cached_dataset())
