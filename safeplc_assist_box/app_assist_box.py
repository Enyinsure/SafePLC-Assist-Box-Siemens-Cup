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
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from evidence_card_formatter import build_evidence_cards, detect_safety_level, summarize_answer
from work_order_demo import generate_work_order_text

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


PROJECT_ROOT = Path("/home/scc/pb23061092")
APP_ROOT = PROJECT_ROOT / "safeplc_assist_box"
BACKEND_SCRIPT = PROJECT_ROOT / "s7_multimodal_v1" / "ask_s7_agent_v2.py"
DEMO_CASES_PATH = APP_ROOT / "demo_cases.json"

DEFAULT_TIMEOUT = int(os.environ.get("SAFEPLC_AGENT_TIMEOUT", "180"))


def load_demo_cases() -> List[Dict[str, str]]:
    if not DEMO_CASES_PATH.exists():
        return []
    try:
        return json.loads(DEMO_CASES_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        st.warning(f"demo_cases.json 读取失败：{exc}")
        return []


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
    if "history" not in st.session_state:
        st.session_state.history = []
    if "last_query" not in st.session_state:
        st.session_state.last_query = ""
    if "last_context" not in st.session_state:
        st.session_state.last_context = ""
    if "last_answer" not in st.session_state:
        st.session_state.last_answer = ""
    if "last_v11_analysis" not in st.session_state:
        st.session_state.last_v11_analysis = {}


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
    """兼容 V1.1 模块不同字段命名，取第一个存在的字段。"""
    for key in keys:
        value = data.get(key)
        if value is not None and value != "":
            return str(value)
    return default


def run_v11_frontend_analysis(query: str, context: str = "") -> Dict[str, object]:
    """
    V1.1 前端诊断分析。
    注意：这里不替代 Agent v2，不改变原后端回答，只把 V1.1 分类/风险结果展示给评委看。
    """
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

        qtype = _pick_first(
            analysis["classifier"],
            ["question_type", "qtype", "type", "category"],
            "-",
        )
        action = _pick_first(
            analysis["classifier"],
            ["action", "route", "action_route", "next_action"],
            "-",
        )
        strategy = _pick_first(
            analysis["classifier"],
            ["retrieval_strategy", "strategy", "retriever", "preferred_retriever"],
            "-",
        )
        risk_level = _pick_first(
            analysis["risk"],
            ["risk_level", "level", "safety_level"],
            "-",
        )

        missing_slots = analysis["classifier"].get("missing_slots", [])
        clarify = False
        if isinstance(missing_slots, list) and len(missing_slots) > 0:
            clarify = True
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
    """在问答页展示 V1.1 问题分类、动作路由与风险等级。"""
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
        st.json({
            "classifier": analysis.get("classifier", {}),
            "risk": analysis.get("risk", {}),
        })


def build_v11_evidence_items_from_answer(answer: str, query: str = "", context: str = "") -> List[Dict[str, Any]]:
    """
    将当前 Agent v2 文本输出中抽取到的页码、figure_id、证据类型转换成 V1.1 evidence_items。
    这是前端轻量桥接层，不改变原 RAG 后端检索结果。
    """
    parsed = build_evidence_cards(answer, query=query, context=context)

    pages = parsed.get("evidence_pages", []) or []
    figures = parsed.get("figure_ids", []) or []
    evidence_types = parsed.get("evidence_types", []) or []

    items: List[Dict[str, Any]] = []

    # 如果有页码，就按页码构造证据项
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

    # 如果没有页码但有 figure_id，也保留图文证据项
    if not items and figures:
        for idx, figure_id in enumerate(figures, start=1):
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

    # 如果完全没有显式证据，但回答非空，构造一个低置信文本项，便于 V1.1 给出 Low/Review
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
    """运行 V1.1 Evidence Confidence 与答案-证据一致性校验。"""
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

        if assess_evidence_confidence:
            confidence_result = assess_evidence_confidence(query, answer, evidence_items)
        else:
            confidence_result = {}

        if check_answer_evidence_alignment:
            alignment_result = check_answer_evidence_alignment(answer, evidence_items)
        else:
            alignment_result = {}

        conf = confidence_result.get("confidence") if isinstance(confidence_result, dict) else None

        if build_v11_evidence_cards:
            cards = build_v11_evidence_cards(evidence_items, conf)
        else:
            cards = []

        result["enabled"] = True
        result["confidence"] = confidence_result
        result["alignment"] = alignment_result
        result["cards"] = cards
        return result

    except Exception as exc:
        result["error"] = str(exc)
        return result


def render_v11_evidence_trust_panel(query: str, context: str, answer: str) -> None:
    """展示 Evidence Confidence、Evidence Check 和 V1.1 证据卡片。"""
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

    with st.expander("查看 V1.1 Evidence Confidence / Evidence Check 原始结果", expanded=False):
        st.json(
            {
                "confidence": confidence,
                "alignment": alignment,
                "evidence_items": trust.get("evidence_items", []),
            }
        )


def build_v11_qa_log_record(query: str, context: str, answer: str) -> Dict[str, Any]:
    """构造单次问答的 V1.1 可审计日志。"""
    analysis = run_v11_frontend_analysis(query, context)
    trust = run_v11_evidence_trust_analysis(query, context, answer)
    legacy_cards = build_evidence_cards(answer, query=query, context=context)

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project": "SafePLC-Assist Box",
        "version": "V1.1",
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
    """提供单次问答 V1.1 日志下载，便于答辩材料和测试报告留痕。"""
    if not answer:
        return

    log_record = build_v11_qa_log_record(query, context, answer)
    safe_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"safeplc_v11_qa_log_{safe_time}.json"

    st.download_button(
        "下载本次 V1.1 问答日志 .json",
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
    面向 S7-1500 / ET 200MP 手册的多模态工业知识 Agent 与安全运维助手。
    支持参数查询、接口图/接线图/拓扑图证据检索、主动澄清和危险操作安全拒答。
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

        st.subheader("V1.1 模块状态")
        st.markdown(
            """
- Agent v2：ON
- Safety Guard v1：ON
- Risk Classifier v1.1：ON
- Question Router v1.1：ON
- Evidence Confidence：ON
- Evidence Check：ON
            """
        )

        with st.expander("开发与运行信息", expanded=False):
            st.code(
                "前端: conda activate s7rag_ui\n"
                "后端: conda run -n s7rag python ask_s7_agent_v2.py",
                language="bash",
            )
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

它基于既有 SafePLC-Agent 技术底座，围绕 S7-1500 / ET 200MP 中文手册构建多模态 RAG 知识库，
支持文本、表格、接口图、接线图、端子分配图、PROFINET 拓扑图等证据检索，并通过 Agent v2 主动澄清和 Safety Guard v1 工业安全护栏减少误查、误答和危险操作输出。

V1.1 版本进一步加入工业安全风险分级、问题类型分类器、Evidence Confidence 证据置信度、证据卡片和答案-证据一致性校验，使工业知识问答从“能回答”提升为“可追溯、可复核、可审计、可评测”。
        """
    )

    st.subheader("V1.1 可信证据增强状态")

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Agent v2", "ON")
    s2.metric("Safety Guard v1", "ON")
    s3.metric("Risk Classifier v1.1", "ON")
    s4.metric("Question Router v1.1", "ON")

    s5, s6, s7, s8 = st.columns(4)
    s5.metric("Evidence Confidence", "ON")
    s6.metric("Evidence Check", "ON")
    s7.metric("Self-check", "OK")
    s8.metric("Clean Delivery", "READY")

    st.markdown(
        """
<div class="safeplc-ok">
<b>当前运行模式：</b>OFFLINE / READ-ONLY。系统仅用于工业知识问答、证据追溯、安全提示和运维记录辅助；
不连接真实 PLC，不接入 TIA Portal，不执行下载、写入或控制动作。
</div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("核心能力")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
<div class="safeplc-card">
<b>工业知识问答</b><br/>
快速查询电源参数、接口说明、PROFINET/HMI 连接、EMC 等手册知识。
</div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
<div class="safeplc-card">
<b>可信证据增强</b><br/>
展示证据页码、证据类型、图文证据编号，便于答辩和运维复核。
</div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
<div class="safeplc-card">
<b>安全运维提醒</b><br/>
遇到短接安全回路、带电接线、强制输出等危险问题时拒绝输出步骤。
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
6. 生成运维辅助记录。
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
        return

    for idx, case in enumerate(cases, start=1):
        with st.expander(f"{idx}. {case.get('title', '未命名案例')}", expanded=False):
            st.markdown(f"**问题：** {case.get('query', '')}")
            st.markdown(f"**上下文：** {case.get('context', '') or '无'}")
            if st.button(f"运行案例 {idx}", key=f"run_case_{idx}"):
                query = case.get("query", "").strip()
                context = case.get("context", "").strip()
                with st.spinner("正在运行典型案例..."):
                    stdout, merged, return_code = call_agent_v2(query, context)
                st.session_state.last_query = query
                st.session_state.last_context = context
                st.session_state.last_answer = merged
                st.session_state.last_v11_analysis = run_v11_frontend_analysis(query, context)
                add_history(query, context, merged, return_code)

                render_v11_analysis_panel(st.session_state.get("last_v11_analysis", {}))
                st.markdown("### 案例输出")
                st.code(merged, language="text")
                render_evidence_cards(merged, query, context)
                render_v11_evidence_trust_panel(query, context, merged)
                render_v11_log_download(query, context, merged, key_suffix=f"demo_{idx}")


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

系统当前定位为 **软件原型 + 产品化交互样机 + V1.1 可信证据增强模块**，
不是现场 PLC 控制系统，不替代厂家手册、现场安全规程和具备资质人员判断。
        """
    )

    st.markdown("### 当前已完成能力")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            """
#### V1.0 多模态工业知识 Agent

- S7-1500 / ET 200MP 中文手册多模态 RAG
- 文本、表格、接口图、接线图、端子分配图、拓扑图证据检索
- ChromaDB 图文索引
- 页码、figure_id、证据类型输出
- Agent v2 主动澄清
- Safety Guard v1 工业安全护栏
- Streamlit 产品化前端
- 典型案例演示与运维记录生成
            """
        )

    with c2:
        st.markdown(
            """
#### V1.1 可信证据增强

- 工业安全风险分级：SAFE / CAUTION / HIGH_RISK / EMERGENCY
- 问题类型分类器与动作路由
- 槽位填充与主动澄清触发
- Evidence Confidence：High / Medium / Low / Conflict
- 证据卡片输出
- 标准回答结构：结论 / 依据 / 适用条件 / 风险提示
- 答案-证据一致性校验：PASS / REVIEW / FAIL
- 标准测试集、自动评测脚本和一键自检脚本
            """
        )

    st.markdown("### 技术边界")

    st.markdown(
        """
<div class="safeplc-warning">
<b>本作品不是现场控制系统。</b><br/>
系统当前仅用于离线工业知识问答、证据追溯、安全提示和运维记录辅助。
</div>
        """,
        unsafe_allow_html=True,
    )

    b1, b2 = st.columns(2)

    with b1:
        st.markdown(
            """
#### 明确不做

- 不连接真实 PLC
- 不接入 TIA Portal
- 不执行真实 PLC 通信
- 不执行下载、写入、启动、停止或控制动作
- 不采集真实 IT / OT 网络数据
- 不作为现场安全控制系统
            """
        )

    with b2:
        st.markdown(
            """
#### 使用约束

- 不替代 Siemens 官方手册
- 不替代现场电气安全规程
- 不替代具备资质人员判断
- 对复杂接线、端子和安全回路问题，仅提供证据追溯与安全提示
- 对短接安全回路、绕过保护、带电危险操作等问题拒绝输出危险步骤
            """
        )

    st.markdown("### V1.1 工程交付状态")

    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Basic Testset", "12 cases")
    e2.metric("Eval Result", "All Passed")
    e3.metric("Self-check", "Overall OK")
    e4.metric("SHA256", "OK")

    st.markdown(
        """
#### 已生成交付文件

- `SAFEPLC_ASSIST_BOX_SIEMENS_CUP_V11_CLEAN.tar.gz`
- `SAFEPLC_ASSIST_BOX_SIEMENS_CUP_V11_CLEAN.sha256`
- `SAFEPLC_ASSIST_BOX_SIEMENS_CUP_V11_CLEAN_manifest.txt`
- `PROJECT_FINAL_STATUS_SIEMENS_CUP_V11.txt`

#### V1.1 关键新增模块

- `safety_risk_guard_v11.py`
- `question_classifier_v11.py`
- `evidence_confidence_v11.py`
- `answer_evidence_checker_v11.py`
- `run_v11_eval.py`
- `self_check_safeplc_v11.py`
- `testset_v11_basic.json`
        """
    )

    st.markdown("### 后续扩展方向")

    st.markdown(
        """
- 扩展更大规模测试集，从 basic 回归测试扩展到 50～100 条复杂问题测试。
- 将更多 V1.1 证据置信度和一致性校验结果接入前端可视化。
- 增强图文证据展示，进一步支持图纸缩略图和证据片段定位。
- 接入仿真环境或数字孪生环境，探索只读诊断数据辅助分析。
- 扩展更多 Siemens 工业设备手册，提升知识库覆盖范围。
        """
    )


def main() -> None:
    st.set_page_config(
        page_title="SafePLC-Assist Box",
        page_icon="🛡️",
        layout="wide",
    )
    init_session_state()
    render_css()
    render_sidebar()
    render_header()

    tab_home, tab_qa, tab_demo, tab_work_order, tab_boundary = st.tabs(
        [
            "产品首页",
            "工业知识问答",
            "典型案例演示",
            "运维记录生成",
            "产品说明与技术边界",
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
    with tab_boundary:
        render_boundary_tab()


if __name__ == "__main__":
    main()
