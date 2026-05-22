#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SafePLC-Assist Box 工业知识安全问答终端

西门子杯自由探索赛道产品化前端。
说明：
1. 不修改原 s7_multimodal_v1 工程。
2. 前端运行在 s7rag_ui 环境。
3. 后端调用复用 s7rag 环境中的 ask_s7_agent_v2.py。
4. 不连接真实 PLC，不执行真实控制动作。
5. 已接入复杂典型案例展示 demo_cases_complex.json。
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

try:
    from evidence_card_formatter import build_evidence_cards, detect_safety_level, summarize_answer
except Exception:
    def build_evidence_cards(answer: str, query: str = "", context: str = "") -> Dict[str, Any]:
        pages = re.findall(r"(?:第\s*)?(\d{1,5})\s*页", answer or "")
        figures = re.findall(r"(?:figure_id|图文证据|图号)[:：]?\s*([A-Za-z0-9_\-]+)", answer or "")
        safety_level = "HIGH_RISK" if any(x in (answer or "") for x in ["HIGH_RISK", "高风险", "拒绝"]) else "UNKNOWN"
        return {
            "safety_level": safety_level,
            "evidence_pages": list(dict.fromkeys(pages)),
            "figure_ids": list(dict.fromkeys(figures)),
            "evidence_types": [],
            "status": "PARSED",
        }

    def detect_safety_level(answer: str) -> str:
        return "HIGH_RISK" if "高风险" in answer or "HIGH_RISK" in answer else "UNKNOWN"

    def summarize_answer(answer: str) -> str:
        return (answer or "")[:200]

try:
    from work_order_demo import generate_work_order_text
except Exception:
    def generate_work_order_text(query: str, context: str, answer: str, operator: str = "SafePLC-Assist Box 演示用户") -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""SafePLC-Assist Box 运维辅助记录

记录时间：{now}
记录人：{operator}

一、用户问题
{query}

二、补充上下文
{context or "无"}

三、系统回答摘要
{answer}

四、风险与边界
本记录由离线只读工业知识问答原型辅助生成，不连接真实 PLC，不执行控制动作。
最终处理结论需由现场具备资质人员结合官方手册、现场图纸和安全规程确认。
"""

# V1.1 增强模块：仅用于前端诊断展示，不改变原 Agent v2 后端链路
try:
    from question_classifier_v11 import classify_question
    from safety_risk_guard_v11 import assess_industrial_risk
except Exception:
    classify_question = None
    assess_industrial_risk = None

try:
    from evidence_confidence_v11 import (
        assess_evidence_confidence,
        build_evidence_cards as build_v11_evidence_cards,
    )
    from answer_evidence_checker_v11 import check_answer_evidence_alignment
except Exception:
    assess_evidence_confidence = None
    build_v11_evidence_cards = None
    check_answer_evidence_alignment = None


# 兼容学校服务器与本地仓库
DEFAULT_PROJECT_ROOT = Path("/home/scc/pb23061092")
if DEFAULT_PROJECT_ROOT.exists():
    PROJECT_ROOT = DEFAULT_PROJECT_ROOT
else:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]

APP_ROOT = PROJECT_ROOT / "safeplc_assist_box"
BACKEND_SCRIPT = PROJECT_ROOT / "s7_multimodal_v1" / "ask_s7_agent_v2.py"
DEMO_CASES_PATH = APP_ROOT / "demo_cases.json"
COMPLEX_DEMO_CASES_PATH = APP_ROOT / "demo_cases_complex.json"

VISUAL_EVIDENCE_DIRS = [
    APP_ROOT / "assets" / "visual_candidate_pages",
    PROJECT_ROOT / "full_restore_agent_v2" / "s7_multimodal_v1" / "images" / "visual_candidate_pages",
    PROJECT_ROOT / "release_selfcheck_agent_v1" / "s7_multimodal_v1" / "images" / "visual_candidate_pages",
    PROJECT_ROOT / "release_selfcheck_format_opt_stress_ok" / "s7_multimodal_v1" / "images" / "visual_candidate_pages",
    PROJECT_ROOT / "release_selfcheck_safety_guard_v1" / "s7_multimodal_v1" / "images" / "visual_candidate_pages",
]

DEFAULT_TIMEOUT = int(os.environ.get("SAFEPLC_AGENT_TIMEOUT", "180"))


def find_visual_evidence_image(page: Any = None, figure_id: Any = None) -> Optional[Path]:
    """根据 evidence card 中的 page 或 figure_id 自动查找图文证据图片。"""
    page_numbers: List[int] = []

    if figure_id not in (None, "", "-"):
        match = re.search(r"page[_-]?(\d+)", str(figure_id), flags=re.IGNORECASE)
        if match:
            try:
                page_numbers.append(int(match.group(1)))
            except ValueError:
                pass

    if page not in (None, "", "-"):
        try:
            page_numbers.append(int(str(page).strip()))
        except ValueError:
            match = re.search(r"(\d+)", str(page))
            if match:
                page_numbers.append(int(match.group(1)))

    seen = set()
    ordered_pages = []
    for n in page_numbers:
        if n not in seen:
            seen.add(n)
            ordered_pages.append(n)

    for n in ordered_pages:
        candidate_names = [
            f"page_{n:04d}.jpg",
            f"page_{n:04d}.jpeg",
            f"page_{n:04d}.png",
            f"page_{n}.jpg",
            f"page_{n}.jpeg",
            f"page_{n}.png",
        ]
        for directory in VISUAL_EVIDENCE_DIRS:
            for name in candidate_names:
                candidate = directory / name
                if candidate.exists():
                    return candidate

    return None


def render_visual_evidence_image(card: Dict[str, Any]) -> None:
    img_path = find_visual_evidence_image(
        page=card.get("page"),
        figure_id=card.get("figure_id"),
    )
    if img_path:
        st.image(str(img_path), caption=f"图文证据图片：{img_path.name}", use_container_width=True)
    elif str(card.get("evidence_type", "")).find("图") >= 0 or card.get("figure_id"):
        st.caption("未找到对应图文证据图片，仅显示页码与 figure_id。")


def load_json_list(path: Path, warning_name: str) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception as exc:
        st.warning(f"{warning_name} 读取失败：{exc}")
        return []


def load_demo_cases() -> List[Dict[str, Any]]:
    return load_json_list(DEMO_CASES_PATH, "demo_cases.json")


def load_complex_demo_cases() -> List[Dict[str, Any]]:
    return load_json_list(COMPLEX_DEMO_CASES_PATH, "demo_cases_complex.json")


def build_backend_command(query: str, context: str) -> List[str]:
    """
    前端在 s7rag_ui 中启动，后端通过 conda run 调用 s7rag 环境。
    可选覆盖：
      export SAFEPLC_BACKEND_PYTHON=/path/to/s7rag/python
    """
    backend_python = os.environ.get("SAFEPLC_BACKEND_PYTHON", "").strip()

    if backend_python:
        cmd = [backend_python, str(BACKEND_SCRIPT), query]
    elif shutil.which("conda"):
        cmd = ["conda", "run", "-n", "s7rag", "python", str(BACKEND_SCRIPT), query]
    else:
        cmd = ["python", str(BACKEND_SCRIPT), query]

    if context.strip():
        cmd.extend(["--context", context.strip()])

    return cmd


def call_agent_v2(query: str, context: str = "") -> Tuple[str, str, int]:
    if not BACKEND_SCRIPT.exists():
        return (
            "",
            f"ERROR: 后端入口不存在：{BACKEND_SCRIPT}",
            127,
        )

    cmd = build_backend_command(query, context)

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=DEFAULT_TIMEOUT,
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        merged = stdout.strip()
        if stderr.strip():
            merged = f"{merged}\n\n[stderr]\n{stderr.strip()}".strip()
        return stdout, merged, result.returncode
    except subprocess.TimeoutExpired:
        return (
            "",
            f"ERROR: 后端调用超时，超过 {DEFAULT_TIMEOUT} 秒。可通过 SAFEPLC_AGENT_TIMEOUT 调整。",
            124,
        )
    except Exception as exc:
        return "", f"ERROR: 后端调用失败：{exc}", 1


def init_session_state() -> None:
    defaults = {
        "history": [],
        "last_query": "",
        "last_context": "",
        "last_answer": "",
        "last_v11_analysis": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def add_history(query: str, context: str, answer: str, return_code: int) -> None:
    cards = build_evidence_cards(answer, query=query, context=context)
    st.session_state.history.insert(
        0,
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "query": query,
            "context": context,
            "answer": answer,
            "return_code": return_code,
            "safety_level": cards.get("safety_level", "UNKNOWN"),
            "evidence_pages": cards.get("evidence_pages", []),
            "evidence_types": cards.get("evidence_types", []),
        },
    )
    st.session_state.history = st.session_state.history[:20]


def _pick_first(data: Dict[str, object], keys: List[str], default: str = "-") -> str:
    for key in keys:
        value = data.get(key)
        if value is not None and value != "":
            return str(value)
    return default


def run_v11_frontend_analysis(query: str, context: str = "") -> Dict[str, object]:
    analysis: Dict[str, object] = {
        "enabled": False,
        "classifier": {},
        "risk": {},
        "error": "",
    }

    try:
        classifier_result = classify_question(query, context) if classify_question else {}
        risk_result = assess_industrial_risk(query, context) if assess_industrial_risk else {}

        analysis["enabled"] = bool(classifier_result or risk_result)
        analysis["classifier"] = classifier_result or {}
        analysis["risk"] = risk_result or {}

        qtype = _pick_first(analysis["classifier"], ["question_type", "qtype", "type", "category"], "-")
        action = _pick_first(analysis["classifier"], ["action", "route", "action_route", "next_action"], "-")
        strategy = _pick_first(
            analysis["classifier"],
            ["retrieval_strategy", "strategy", "retriever", "preferred_retriever"],
            "-",
        )
        risk_level = _pick_first(analysis["risk"], ["risk_level", "level", "safety_level"], "-")

        missing_slots = analysis["classifier"].get("missing_slots", [])
        clarify = bool(isinstance(missing_slots, list) and len(missing_slots) > 0)
        if str(action).upper() == "CLARIFY":
            clarify = True

        analysis["summary"] = {
            "question_type": qtype,
            "action_route": action,
            "risk_level": risk_level,
            "clarify": "是" if clarify else "否",
            "retrieval_strategy": strategy,
        }
        return analysis

    except Exception as exc:
        analysis["error"] = str(exc)
        return analysis


def render_v11_analysis_panel(analysis: Dict[str, object]) -> None:
    if not analysis:
        return

    st.markdown("### V1.1 分析面板")

    if analysis.get("error"):
        st.warning(f"V1.1 分析模块运行异常：{analysis.get('error')}")
        return

    if not analysis.get("enabled"):
        st.info("V1.1 分析模块未启用或未返回结果。")
        return

    summary = analysis.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("问题类型", summary.get("question_type", "-"))
    c2.metric("动作路由", summary.get("action_route", "-"))
    c3.metric("风险等级", summary.get("risk_level", "-"))
    c4.metric("触发澄清", summary.get("clarify", "-"))
    c5.metric("检索策略", summary.get("retrieval_strategy", "-"))

    risk_level = str(summary.get("risk_level", "")).upper()
    action_route = str(summary.get("action_route", "")).upper()

    if risk_level in {"HIGH_RISK", "EMERGENCY"} or action_route == "SAFETY_GUARD":
        st.markdown(
            '<div class="safeplc-warning"><b>V1.1 Safety Guard：</b>该问题被识别为高风险或应急类请求，系统应拒绝输出危险操作步骤，并提供安全替代排查方向。</div>',
            unsafe_allow_html=True,
        )
    elif action_route == "CLARIFY":
        st.markdown(
            '<div class="safeplc-warning"><b>V1.1 Agent Clarify：</b>该问题缺少关键槽位，系统应优先追问型号、订货号、接口名或参数名，避免盲目检索。</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="safeplc-ok"><b>V1.1 Routing：</b>该问题可进入知识检索或标准回答流程，并保留证据追溯信息。</div>',
            unsafe_allow_html=True,
        )

    with st.expander("查看 V1.1 原始分类与风险结果", expanded=False):
        st.json(
            {
                "classifier": analysis.get("classifier", {}),
                "risk": analysis.get("risk", {}),
            }
        )


def build_v11_evidence_items_from_answer(answer: str, query: str = "", context: str = "") -> List[Dict[str, Any]]:
    parsed = build_evidence_cards(answer, query=query, context=context)

    pages = parsed.get("evidence_pages", []) or []
    figures = parsed.get("figure_ids", []) or []
    evidence_types = parsed.get("evidence_types", []) or []

    items: List[Dict[str, Any]] = []

    for idx, page in enumerate(pages, start=1):
        ev_type = "text"
        if evidence_types:
            ev_type = str(evidence_types[min(idx - 1, len(evidence_types) - 1)])
        figure_id = figures[idx - 1] if idx - 1 < len(figures) else None

        items.append(
            {
                "source": "S7-1500 / ET 200MP 中文手册",
                "page": page,
                "evidence_type": ev_type,
                "figure_id": figure_id,
                "title": "Agent v2 输出证据",
                "module": context or "",
                "parameter": query or "",
                "text": answer,
            }
        )

    if not items and figures:
        for figure_id in figures:
            items.append(
                {
                    "source": "S7-1500 / ET 200MP 中文手册",
                    "page": None,
                    "evidence_type": "figure",
                    "figure_id": figure_id,
                    "title": "Agent v2 图文证据",
                    "module": context or "",
                    "parameter": query or "",
                    "text": answer,
                }
            )

    if not items and answer.strip():
        items.append(
            {
                "source": "Agent v2 answer text",
                "page": None,
                "evidence_type": "answer_text",
                "figure_id": None,
                "title": "未抽取到显式页码或 figure_id",
                "module": context or "",
                "parameter": query or "",
                "text": answer,
            }
        )

    return items


def run_v11_evidence_trust_analysis(query: str, context: str, answer: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "enabled": False,
        "evidence_items": [],
        "confidence": {},
        "alignment": {},
        "cards": [],
        "error": "",
    }

    try:
        evidence_items = build_v11_evidence_items_from_answer(answer, query=query, context=context)
        result["evidence_items"] = evidence_items

        confidence_result = assess_evidence_confidence(query, answer, evidence_items) if assess_evidence_confidence else {}
        alignment_result = check_answer_evidence_alignment(answer, evidence_items) if check_answer_evidence_alignment else {}

        conf = confidence_result.get("confidence") if isinstance(confidence_result, dict) else None
        cards = build_v11_evidence_cards(evidence_items, conf) if build_v11_evidence_cards else []

        result["enabled"] = True
        result["confidence"] = confidence_result
        result["alignment"] = alignment_result
        result["cards"] = cards
        return result

    except Exception as exc:
        result["error"] = str(exc)
        return result


def render_v11_evidence_trust_panel(query: str, context: str, answer: str) -> None:
    if not answer:
        return

    trust = run_v11_evidence_trust_analysis(query, context, answer)

    st.markdown("### V1.1 证据可信面板")

    if trust.get("error"):
        st.warning(f"V1.1 证据可信分析运行异常：{trust.get('error')}")
        return

    if not trust.get("enabled"):
        st.info("V1.1 证据可信分析未启用。")
        return

    confidence = trust.get("confidence", {})
    alignment = trust.get("alignment", {})

    if not isinstance(confidence, dict):
        confidence = {}
    if not isinstance(alignment, dict):
        alignment = {}

    conf_value = confidence.get("confidence", "-")
    conf_reason = confidence.get("reason", "-")
    verdict = alignment.get("verdict", "-")
    support_rate = alignment.get("support_rate", "-")

    c1, c2, c3 = st.columns(3)
    c1.metric("Evidence Confidence", conf_value)
    c2.metric("Evidence Check", verdict)
    c3.metric("Support Rate", support_rate)

    if str(verdict).upper() == "PASS" and str(conf_value).lower() == "high":
        st.markdown(
            '<div class="safeplc-ok"><b>可信证据结果：</b>答案关键声明基本可由当前证据支撑，可进入人工复核或教学演示流程。</div>',
            unsafe_allow_html=True,
        )
    elif str(verdict).upper() in {"REVIEW", "FAIL"} or str(conf_value).lower() in {"low", "conflict"}:
        st.markdown(
            '<div class="safeplc-warning"><b>可信证据结果：</b>部分关键声明未完全闭合，建议人工复核，不应作为现场操作依据。</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="safeplc-ok"><b>可信证据结果：</b>系统已完成证据置信度与答案一致性检查。</div>',
            unsafe_allow_html=True,
        )

    st.markdown(f"**置信度原因：** {conf_reason}")

    unsupported = alignment.get("unsupported_claims", [])
    if unsupported:
        st.markdown("**未闭合关键声明**")
        st.markdown(
            " ".join([f'<span class="safeplc-badge">{x}</span>' for x in unsupported]),
            unsafe_allow_html=True,
        )

    missing = confidence.get("missing", [])
    if missing:
        st.markdown("**证据中缺失的问题关键词 / 型号项**")
        st.markdown(
            " ".join([f'<span class="safeplc-badge">{x}</span>' for x in missing]),
            unsafe_allow_html=True,
        )

    cards = trust.get("cards", [])
    if cards:
        with st.expander("查看 V1.1 证据卡片", expanded=False):
            for card in cards:
                if not isinstance(card, dict):
                    continue
                st.markdown(
                    f"""
**{card.get('card_id', '-')} | {card.get('evidence_type', '-')} | confidence={card.get('confidence', '-')}**

- page: `{card.get('page', '-')}`
- figure_id: `{card.get('figure_id', '-')}`
- source: `{card.get('source', '-')}`
- title: `{card.get('title', '-')}`
- module: `{card.get('module', '-')}`
- parameter: `{card.get('parameter', '-')}`

{card.get('snippet', '')}
                    """
                )
                render_visual_evidence_image(card)

    with st.expander("查看 V1.1 Evidence Confidence / Evidence Check 原始结果", expanded=False):
        st.json(
            {
                "confidence": confidence,
                "alignment": alignment,
                "evidence_items": trust.get("evidence_items", []),
            }
        )


def build_v11_qa_log_record(query: str, context: str, answer: str) -> Dict[str, Any]:
    analysis = run_v11_frontend_analysis(query, context)
    trust = run_v11_evidence_trust_analysis(query, context, answer)
    legacy_cards = build_evidence_cards(answer, query=query, context=context)

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project": "SafePLC-Assist Box",
        "version": "V1.2",
        "mode": "OFFLINE_READ_ONLY",
        "query": query,
        "context": context,
        "answer": answer,
        "v11_analysis": analysis,
        "v11_evidence_trust": {
            "confidence": trust.get("confidence", {}),
            "alignment": trust.get("alignment", {}),
            "cards": trust.get("cards", []),
            "evidence_items": trust.get("evidence_items", []),
            "error": trust.get("error", ""),
        },
        "legacy_evidence_summary": legacy_cards,
        "technical_boundary": {
            "connect_real_plc": False,
            "tia_portal_integration": False,
            "plc_write_or_control": False,
            "real_it_ot_data_collection": False,
        },
    }


def render_v11_log_download(query: str, context: str, answer: str, key_suffix: str = "qa") -> None:
    if not answer:
        return

    log_record = build_v11_qa_log_record(query, context, answer)
    safe_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"safeplc_v12_qa_log_{safe_time}.json"

    st.download_button(
        "下载本次问答日志 .json",
        data=json.dumps(log_record, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name=filename,
        mime="application/json",
        key=f"download_v11_log_{key_suffix}_{safe_time}",
    )


def render_css() -> None:
    st.markdown(
        """
<style>
.safeplc-hero {
    padding: 1.2rem 1.4rem;
    border-radius: 18px;
    background: linear-gradient(135deg, #f6f8fb 0%, #e8eef8 100%);
    border: 1px solid #d8e0ee;
    margin-bottom: 1rem;
}
.safeplc-title {
    font-size: 2rem;
    font-weight: 800;
    margin-bottom: .35rem;
}
.safeplc-subtitle {
    color: #405166;
    font-size: 1.03rem;
    line-height: 1.65;
}
.safeplc-card {
    padding: 1rem;
    border-radius: 14px;
    border: 1px solid #dde4ef;
    background: #ffffff;
    margin-bottom: .8rem;
}
.safeplc-badge {
    display: inline-block;
    padding: .25rem .55rem;
    border-radius: 999px;
    background: #eef4ff;
    border: 1px solid #d7e5ff;
    font-size: .85rem;
    margin-right: .35rem;
    margin-bottom: .35rem;
}
.safeplc-warning {
    padding: .8rem 1rem;
    border-radius: 12px;
    background: #fff7ed;
    border: 1px solid #fed7aa;
}
.safeplc-ok {
    padding: .8rem 1rem;
    border-radius: 12px;
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
<div class="safeplc-hero">
  <div class="safeplc-title">SafePLC-Assist Box 工业知识安全问答终端</div>
  <div class="safeplc-subtitle">
    面向 S7-1500 / ET 200MP 手册的离线安全问答终端原型。
    支持参数查询、接口图/接线图/拓扑图证据检索、主动澄清、危险操作安全拒答和复杂典型案例展示。
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    with st.sidebar:
        st.header("SafePLC-Assist Box")
        st.caption("西门子杯自由探索赛道 · 产品化样机")

        st.subheader("运行模式")
        st.markdown(
            """
<div class="safeplc-ok">
<b>OFFLINE / READ-ONLY</b><br/>
仅用于工业知识问答、证据追溯、安全提示和运维记录辅助。
</div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("安全边界")
        st.markdown(
            """
- 不连接真实 PLC
- 不接入 TIA Portal
- 不执行下载、写入或控制动作
- 不采集真实 IT / OT 网络数据
- 不替代厂家手册与具备资质人员判断
            """
        )

        st.subheader("模块状态")
        st.markdown(
            """
- Agent v2：ON
- Safety Guard：ON
- Risk Classifier：ON
- Question Router：ON
- Evidence Confidence：ON
- Evidence Check：ON
- Complex Demo Cases：ON
            """
        )

        with st.expander("开发与运行信息", expanded=False):
            st.code(
                "前端: conda activate s7rag_ui\n"
                "后端: conda run -n s7rag python ask_s7_agent_v2.py",
                language="bash",
            )
            st.caption("项目根目录")
            st.caption(str(PROJECT_ROOT))
            st.caption("后端入口")
            st.caption(str(BACKEND_SCRIPT))


def render_evidence_cards(answer: str, query: str = "", context: str = "") -> None:
    cards = build_evidence_cards(answer, query=query, context=context)

    safety_level = cards.get("safety_level", "UNKNOWN")
    pages = cards.get("evidence_pages", [])
    figures = cards.get("figure_ids", [])
    evidence_types = cards.get("evidence_types", [])
    status = cards.get("status", "UNKNOWN")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("安全等级", safety_level)
    c2.metric("证据页码数", len(pages))
    c3.metric("图文证据数", len(figures))
    c4.metric("状态", status)

    st.markdown("#### 证据与安全卡片")

    if safety_level == "HIGH_RISK":
        st.markdown(
            '<div class="safeplc-warning">系统判断为高风险问题：不输出危险操作步骤，仅给出安全替代建议。</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="safeplc-ok">系统已尝试基于手册证据回答，并保留页码、图文证据或安全提示。</div>',
            unsafe_allow_html=True,
        )

    if pages:
        st.markdown("**证据页码**")
        st.markdown(" ".join([f'<span class="safeplc-badge">第 {p} 页</span>' for p in pages]), unsafe_allow_html=True)

    if figures:
        st.markdown("**图文证据 / figure_id**")
        st.markdown(" ".join([f'<span class="safeplc-badge">{f}</span>' for f in figures]), unsafe_allow_html=True)

    if evidence_types:
        st.markdown("**证据类型**")
        st.markdown(" ".join([f'<span class="safeplc-badge">{t}</span>' for t in evidence_types]), unsafe_allow_html=True)


def render_home_tab() -> None:
    st.subheader("产品定位")
    st.markdown(
        """
SafePLC-Assist Box 是面向智能制造现场、新人工程师培训、高校实训教学和设备维护辅助场景的工业知识安全问答终端。

系统围绕 S7-1500 / ET 200MP 中文手册构建工业知识问答能力，支持文本、表格、接口图、接线图、端子分配图、PROFINET 拓扑图等证据检索，并通过主动澄清和安全护栏减少误查、误答和危险操作输出。

当前版本进一步加入复杂典型案例展示，用于证明系统不只支持固定单点问答，也覆盖多条件、多对象、多图文证据、高风险混合请求和运维记录等更通用场景。
        """
    )

    st.subheader("状态控制台")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Agent v2", "ON")
    s2.metric("Safety Guard", "ON")
    s3.metric("Evidence Check", "ON")
    s4.metric("Complex Cases", "ON")

    s5, s6, s7, s8 = st.columns(4)
    s5.metric("运行模式", "OFFLINE")
    s6.metric("PLC 控制", "DISABLED")
    s7.metric("Self-check", "OK")
    s8.metric("Clean Delivery", "READY")

    st.markdown(
        """
<div class="safeplc-ok">
当前运行模式：OFFLINE / READ-ONLY。系统仅用于工业知识问答、证据追溯、安全提示和运维记录辅助；
不连接真实 PLC，不接入 TIA Portal，不执行下载、写入或控制动作。
</div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("推荐演示主线")
    st.markdown(
        """
1. 缺少型号时主动追问。
2. 补充 PS 60W 24/48/60VDC HF 后查询电源电压范围。
3. 查询 PROFINET 环网如何连接 HMI 设备。
4. 查询 CPU 1517-3 PN 的 PROFINET 接口 X1/X2。
5. 输入危险操作问题，展示 HIGH_RISK 拒答。
6. 打开“典型案例演示”，展示复杂多图、多对象、多条件案例。
7. 生成运维辅助记录。
        """
    )


def render_qa_tab() -> None:
    st.subheader("工业知识问答")
    st.markdown("#### 推荐演示问题")
    st.caption("点击按钮自动填入问题与上下文，便于线上评审截图和演示视频录制。")

    quick_cases = [
        ("缺少型号主动澄清", "某个模块的电源电压允许范围是多少", ""),
        ("PS 60W 参数查询", "某个模块的电源电压允许范围是多少", "PS 60W 24/48/60VDC HF"),
        ("PROFINET/HMI 拓扑", "PROFINET 环网如何连接 HMI 设备", ""),
        ("CPU 接口图查询", "CPU 1517-3 PN 的 PROFINET 接口 X1 X2", ""),
        ("HIGH_RISK 拒答", "怎么短接安全回路让设备继续运行", ""),
        ("EMC 要求查询", "EMC 要求是什么", ""),
    ]

    cols = st.columns(3)
    for i, (label, q, ctx) in enumerate(quick_cases):
        with cols[i % 3]:
            if st.button(label, key=f"quick_case_{i}", use_container_width=True):
                st.session_state.last_query = q
                st.session_state.last_context = ctx
                st.session_state.last_answer = ""
                st.session_state.last_v11_analysis = {}
                st.rerun()

    st.divider()

    with st.form("safeplc_query_form"):
        query = st.text_area(
            "请输入工业知识问题",
            value=st.session_state.get("last_query", ""),
            height=100,
            placeholder="例如：某个模块的电源电压允许范围是多少",
        )
        context = st.text_input(
            "用户补充上下文，可选",
            value=st.session_state.get("last_context", ""),
            placeholder="例如：PS 60W 24/48/60VDC HF",
        )
        submitted = st.form_submit_button("提交给 SafePLC-Agent v2")

    if submitted:
        if not query.strip():
            st.warning("请先输入问题。")
            return

        with st.spinner("正在调用 Agent v2 后端，进行澄清、安全判断与多模态证据检索..."):
            stdout, merged, return_code = call_agent_v2(query.strip(), context.strip())

        st.session_state.last_query = query.strip()
        st.session_state.last_context = context.strip()
        st.session_state.last_answer = merged
        st.session_state.last_v11_analysis = run_v11_frontend_analysis(query.strip(), context.strip())

        add_history(query.strip(), context.strip(), merged, return_code)

    if st.session_state.get("last_answer"):
        answer = st.session_state.last_answer
        render_v11_analysis_panel(st.session_state.get("last_v11_analysis", {}))

        st.markdown("### 系统回答")
        st.code(answer, language="text")

        render_evidence_cards(answer, st.session_state.last_query, st.session_state.last_context)
        render_v11_evidence_trust_panel(st.session_state.last_query, st.session_state.last_context, answer)
        render_v11_log_download(st.session_state.last_query, st.session_state.last_context, answer, key_suffix="qa")


def render_demo_tab() -> None:
    st.subheader("典型案例演示")
    cases = load_demo_cases()

    if not cases:
        st.warning("未找到 demo_cases.json。")
    else:
        for idx, case in enumerate(cases, start=1):
            title = case.get("title", f"案例 {idx}")
            query = case.get("query", case.get("user_question", ""))
            context = case.get("context", "")

            with st.expander(f"{idx}. {title}", expanded=False):
                st.markdown(f"**问题：** {query}")
                st.markdown(f"**上下文：** {context or '无'}")

                if st.button(f"运行案例 {idx}", key=f"run_case_{idx}"):
                    with st.spinner("正在运行典型案例..."):
                        stdout, merged, return_code = call_agent_v2(query.strip(), context.strip())

                    st.session_state.last_query = query.strip()
                    st.session_state.last_context = context.strip()
                    st.session_state.last_answer = merged
                    st.session_state.last_v11_analysis = run_v11_frontend_analysis(query.strip(), context.strip())

                    add_history(query.strip(), context.strip(), merged, return_code)

                    render_v11_analysis_panel(st.session_state.get("last_v11_analysis", {}))
                    st.markdown("### 案例输出")
                    st.code(merged, language="text")
                    render_evidence_cards(merged, query, context)
                    render_v11_evidence_trust_panel(query, context, merged)
                    render_v11_log_download(query, context, merged, key_suffix=f"demo_{idx}")

    st.divider()
    render_complex_demo_cases_panel()


# ============================================================
# Complex Demo Cases Panel for Siemens Cup Review
# Added for more general and complex industrial review scenarios
# ============================================================
def render_complex_demo_cases_panel() -> None:
    st.markdown("## 复杂典型案例展示")
    st.caption("用于展示系统面对多条件、多对象、多图文证据、高风险混合请求等更通用场景时的处理能力。")

    complex_cases = load_complex_demo_cases()

    if not complex_cases:
        st.warning("未找到 demo_cases_complex.json，请确认文件已放在 safeplc_assist_box/ 目录下。")
        return

    titles = [
        f"{case.get('id', '')}｜{case.get('title', '')}"
        for case in complex_cases
    ]

    selected_title = st.selectbox(
        "选择复杂典型案例",
        titles,
        key="complex_demo_case_selector",
    )

    selected_case = complex_cases[titles.index(selected_title)]

    st.markdown("### 用户复杂提问")
    st.info(selected_case.get("user_question", ""))

    col1, col2, col3 = st.columns(3)
    col1.metric("问题类型", selected_case.get("expected_question_type", ""))
    col2.metric("系统动作", selected_case.get("expected_action", ""))
    col3.metric("风险等级", selected_case.get("expected_risk_level", ""))

    evidence_types = selected_case.get("expected_evidence_types", [])
    if evidence_types:
        st.markdown("### 预期证据类型")
        for item in evidence_types:
            st.markdown(f"- {item}")

    answer_points = selected_case.get("expected_answer_points", [])
    if answer_points:
        st.markdown("### 预期回答要点")
        for item in answer_points:
            st.markdown(f"- {item}")

    run_complex = st.button("将该复杂问题填入工业知识问答页", key="fill_complex_case")
    if run_complex:
        st.session_state.last_query = selected_case.get("user_question", "")
        st.session_state.last_context = ""
        st.session_state.last_answer = ""
        st.session_state.last_v11_analysis = {}
        st.success("已填入工业知识问答页，请切换到“工业知识问答”提交运行。")

    st.markdown("---")
    st.caption(
        "说明：该区域用于比赛评审展示，证明系统不只支持固定单点问答，"
        "也覆盖复杂工业查询、故障排查、多证据返回和安全风险识别。"
    )


def render_work_order_tab() -> None:
    st.subheader("运维记录生成")

    if not st.session_state.history:
        st.info("暂无问答记录。请先在“工业知识问答”或“典型案例演示”中运行一次查询。")
        return

    selected_index = st.selectbox(
        "选择一条问答记录",
        options=list(range(len(st.session_state.history))),
        format_func=lambda i: f"{st.session_state.history[i]['time']} | {st.session_state.history[i]['query'][:40]}",
    )

    item = st.session_state.history[selected_index]
    operator = st.text_input("记录人 / 演示人", value="SafePLC-Assist Box 演示用户")

    work_order = generate_work_order_text(
        query=item["query"],
        context=item["context"],
        answer=item["answer"],
        operator=operator,
    )

    st.markdown("### 运维辅助记录")
    st.code(work_order, language="text")

    st.download_button(
        "下载运维辅助记录 .txt",
        data=work_order.encode("utf-8"),
        file_name=f"safeplc_work_order_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
    )


def render_boundary_tab() -> None:
    st.subheader("产品说明与技术边界")

    st.markdown(
        """
### 作品定位

SafePLC-Assist Box 是面向 S7-1500 / ET 200MP 中文手册的工业知识安全问答终端，
服务于高校实训教学、新人工程师培训和设备维护辅助场景。

系统当前定位为 **软件原型 + 产品化交互样机 + 可信证据增强模块 + 复杂典型案例展示**，
不是现场 PLC 控制系统，不替代厂家手册、现场安全规程和具备资质人员判断。
        """
    )

    st.markdown("### 当前已完成能力")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            """
#### 多模态工业知识问答

- S7-1500 / ET 200MP 中文手册知识查询
- 文本、表格、接口图、接线图、端子分配图、拓扑图证据检索
- 页码、figure_id、证据类型输出
- Agent 主动澄清
- Safety Guard 工业安全护栏
- Streamlit 产品化前端
            """
        )

    with c2:
        st.markdown(
            """
#### 可信证据与复杂案例增强

- 工业安全风险分级：SAFE / CAUTION / HIGH_RISK / EMERGENCY
- 问题类型分类器与动作路由
- Evidence Confidence：High / Medium / Low / Conflict
- 答案-证据一致性校验：PASS / REVIEW / FAIL
- 复杂典型案例：多条件、多对象、多图像证据、高风险混合请求
- 运维记录生成和日志导出
            """
        )

    st.markdown("### 技术边界")
    st.markdown(
        """
本作品不是现场控制系统。系统当前仅用于离线工业知识问答、证据追溯、安全提示和运维记录辅助。

明确不做以下事项：

- 不连接真实 PLC
- 不接入 TIA Portal
- 不执行真实 PLC 通信
- 不执行下载、写入、启动、停止或控制动作
- 不采集真实 IT / OT 网络数据
- 不作为现场安全控制系统
- 不替代 Siemens 官方手册
- 不替代现场电气安全规程
- 不替代具备资质人员判断
        """
    )


def render_history_tab() -> None:
    st.subheader("最近问答记录")

    if not st.session_state.history:
        st.info("暂无问答记录。")
        return

    for item in st.session_state.history:
        with st.expander(f"{item['time']} | {item['query'][:60]}", expanded=False):
            st.markdown(f"**问题：** {item['query']}")
            st.markdown(f"**上下文：** {item['context'] or '无'}")
            st.markdown(f"**返回码：** {item['return_code']}")
            st.markdown(f"**安全等级：** {item.get('safety_level', '-')}")
            st.code(item["answer"], language="text")


def main() -> None:
    st.set_page_config(
        page_title="SafePLC-Assist Box",
        page_icon="🧰",
        layout="wide",
    )

    init_session_state()
    render_css()
    render_header()
    render_sidebar()

    tab_home, tab_qa, tab_demo, tab_work_order, tab_history, tab_boundary = st.tabs(
        [
            "首页",
            "工业知识问答",
            "典型案例演示",
            "运维记录生成",
            "问答记录",
            "技术边界",
        ]
    )

    with tab_home:
        render_home_tab()

    with tab_qa:
        render_qa_tab()

    with tab_demo:
        render_demo_tab()

    with tab_work_order:
        render_work_order_tab()

    with tab_history:
        render_history_tab()

    with tab_boundary:
        render_boundary_tab()


if __name__ == "__main__":
    main()
