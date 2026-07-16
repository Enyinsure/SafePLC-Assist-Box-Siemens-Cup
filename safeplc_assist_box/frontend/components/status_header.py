"""Top operational status header."""

from __future__ import annotations

from typing import Any, Mapping

import streamlit as st

from .common import detection_source_label, esc, status_class


def render_status_header(
    runtime: Mapping[str, Any],
    device_context: Mapping[str, str],
    query_status: str,
) -> None:
    frontend_mode = str(runtime.get("frontend_mode") or "auto").upper()
    mode_label = f"{frontend_mode} / {runtime.get('pipeline_mode', '')}"
    device = str(device_context.get("model") or "自动识别")
    detection_source = detection_source_label(device_context.get("detection_source"))
    items = [
        ("系统", runtime.get("system", "未知"), _runtime_class(runtime.get("system"))),
        ("运行模式", mode_label, "status-neutral" if frontend_mode != "DEMO" else "status-warning"),
        ("结果来源", runtime.get("result_source_label", "尚未查询"), _runtime_class(runtime.get("result_source_label"))),
        ("Text Chroma", runtime.get("text_chroma", "未知"), _runtime_class(runtime.get("text_chroma"))),
        ("Figure Chroma", runtime.get("figure_chroma", "未知"), _runtime_class(runtime.get("figure_chroma"))),
        ("模型", runtime.get("model", "未知"), _runtime_class(runtime.get("model"))),
        ("当前设备", device, "status-neutral"),
        ("识别来源", detection_source, "status-neutral"),
        ("查询", query_status, _runtime_class(query_status)),
    ]
    cells = "".join(
        (
            '<div class="runtime-cell">'
            f'<span class="runtime-label">{esc(label)}</span>'
            f'<span class="runtime-value {css_class}"><span class="status-dot"></span>{esc(value)}</span>'
            "</div>"
        )
        for label, value, css_class in items
    )
    st.markdown(
        f"""
        <header class="safeplc-header">
          <div class="brand-lockup">
            <div class="brand-mark">SP</div>
            <div>
              <h1>SafePLC-Assist Box</h1>
              <p>面向 PLC 教学实训与维护查证的动态多智能体协作终端</p>
            </div>
          </div>
          <div class="runtime-grid">{cells}</div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def _runtime_class(value: Any) -> str:
    text = str(value or "").lower()
    if any(
        token in text
        for token in ("未配置", "无效", "不可用", "失败", "异常", "error", "unavailable")
    ):
        return "status-fail"
    if any(token in text for token in ("待", "演示", "sample", "运行中", "查询中", "pending")):
        return "status-warning"
    if any(
        token in text
        for token in ("已连接", "可用", "正常", "完成", "connected", "available")
    ):
        return "status-pass"
    return status_class(text)
