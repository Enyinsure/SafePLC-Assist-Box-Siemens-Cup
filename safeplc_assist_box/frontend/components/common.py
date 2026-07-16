"""Shared visual primitives."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

import streamlit as st

from ..paths import ASSET_ROOT


STATUS_LABELS = {
    "passed": "通过",
    "warning": "警告",
    "failed": "失败",
    "not_checked": "未检查",
    "completed": "已完成",
    "waiting": "等待",
    "skipped": "跳过",
    "running": "执行中",
    "high": "高",
    "medium": "中",
    "low": "低",
    "unknown": "未知",
}

DETECTION_SOURCE_LABELS = {
    "user_selected": "用户选择",
    "query_auto_detected": "查询自动识别",
    "auto_detected": "查询自动识别",
    "evidence_inferred": "证据推断",
    "demo_fixed": "离线案例固定",
    "unknown": "未识别",
}


def load_styles(path: Path = ASSET_ROOT / "styles.css") -> None:
    try:
        css = path.read_text(encoding="utf-8")
    except OSError:
        return
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def status_class(status: str) -> str:
    value = str(status or "").lower()
    if value in {"passed", "completed", "pass", "answered", "ok", "high"}:
        return "status-pass"
    if value in {"warning", "partial", "review", "medium", "waiting", "running"}:
        return "status-warning"
    if value in {"failed", "fail", "conflict", "refuse", "error", "low"}:
        return "status-fail"
    return "status-neutral"


def status_label(status: str) -> str:
    return STATUS_LABELS.get(str(status or "").lower(), str(status or "未检查"))


def detection_source_label(source: Any) -> str:
    return DETECTION_SOURCE_LABELS.get(str(source or "").lower(), str(source or "未识别"))


def badge(status: str, label: str | None = None) -> str:
    return (
        f'<span class="status-badge {status_class(status)}">'
        f'<span class="status-dot"></span>{esc(label or status_label(status))}</span>'
    )


def section_heading(title: str, eyebrow: str = "") -> None:
    eyebrow_html = f'<span class="section-eyebrow">{esc(eyebrow)}</span>' if eyebrow else ""
    st.markdown(
        f'<div class="section-heading">{eyebrow_html}<h2>{esc(title)}</h2></div>',
        unsafe_allow_html=True,
    )


def empty_state(title: str, detail: str = "") -> None:
    detail_html = f"<p>{esc(detail)}</p>" if detail else ""
    st.markdown(
        f'<div class="empty-state"><strong>{esc(title)}</strong>{detail_html}</div>',
        unsafe_allow_html=True,
    )


def format_score(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "未提供"
    return f"{numeric:.3f}" if numeric else "未提供"
