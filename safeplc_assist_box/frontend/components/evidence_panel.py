"""Shared Evidence Pool cards with safe image handling."""

from __future__ import annotations

from typing import Any, Mapping

import streamlit as st

from ..paths import resolve_project_path
from .common import badge, esc, format_score, section_heading


def render_evidence_pool(result: Mapping[str, Any]) -> None:
    stats = dict(result.get("evidence_stats") or {})
    evidences = list(result.get("evidence_pool") or [])
    rejected = list(result.get("rejected_evidence") or [])
    section_heading("Shared Evidence Pool", "EVIDENCE")
    st.markdown(
        f"""
        <div class="evidence-stats">
          <div><span>证据池</span><strong>{int(stats.get('total') or 0)}</strong></div>
          <div><span>文本</span><strong>{int(stats.get('text') or 0)}</strong></div>
          <div><span>图示</span><strong>{int(stats.get('figure') or 0)}</strong></div>
          <div><span>参数表</span><strong>{int(stats.get('table') or 0)}</strong></div>
          <div><span>型号一致</span><strong>{int(stats.get('model_consistent') or 0)}/{int(stats.get('model_checked') or 0)}</strong></div>
          <div><span>跨型号拦截</span><strong>{int(stats.get('cross_model_blocked') or 0)}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not evidences:
        st.info("本次查询没有收集到证据。")
    for evidence in evidences:
        _render_evidence_card(evidence)

    with st.expander(f"已拦截证据 · {len(rejected)}", expanded=False):
        if not rejected:
            st.write("本次 Evidence Pool 未记录被拦截证据。")
        else:
            for item in rejected:
                st.markdown(
                    f"**{item.get('display_id') or item.get('evidence_id') or '未编号'}** · "
                    f"{item.get('reason') or '未记录原因'} · 页码 {item.get('page') or '未提供'}"
                )


def _render_evidence_card(evidence: Mapping[str, Any]) -> None:
    accepted_status = "passed" if evidence.get("accepted") else "warning"
    model_value = evidence.get("model_consistent")
    model_label = "通过" if model_value is True else ("失败" if model_value is False else "未检查")
    model_status = "passed" if model_value is True else ("failed" if model_value is False else "not_checked")
    safety_value = evidence.get("safety_checked")
    safety_label = "通过" if safety_value is True else ("失败" if safety_value is False else "未检查")
    safety_status = "passed" if safety_value is True else ("failed" if safety_value is False else "not_checked")
    location = " / ".join(
        value
        for value in (
            f"第 {evidence.get('page')} 页" if evidence.get("page") is not None else "",
            str(evidence.get("figure_number") or evidence.get("section") or ""),
        )
        if value
    ) or "位置未提供"
    claims = "、".join(evidence.get("supports_claims") or []) or "未关联结构化 claim"
    st.markdown(
        f"""
        <article class="evidence-card">
          <div class="evidence-card-head">
            <div><span class="evidence-id">{esc(evidence.get('display_id'))}</span><strong>{esc(evidence.get('document_name'))}</strong></div>
            {badge(accepted_status, 'Judge 采用' if evidence.get('accepted') else '候选证据')}
          </div>
          <div class="evidence-meta">
            <span>{esc(evidence.get('modality'))}</span>
            <span>{esc(evidence.get('retriever'))}</span>
            <span>{esc(location)}</span>
            <span>支持强度 {esc(evidence.get('confidence_level'))}</span>
          </div>
          <p>{esc(evidence.get('excerpt'))}</p>
          <dl>
            <dt>设备型号</dt><dd>{esc(evidence.get('model') or '未提供')}</dd>
            <dt>设备系列</dt><dd>{esc(evidence.get('family') or '未提供')}</dd>
            <dt>订货号</dt><dd>{esc(evidence.get('order_number') or '未提供')}</dd>
            <dt>支持结论</dt><dd>{esc(claims)}</dd>
            <dt>型号一致性</dt><dd>{badge(model_status, model_label)}</dd>
            <dt>安全检查</dt><dd>{badge(safety_status, safety_label)}</dd>
          </dl>
        </article>
        """,
        unsafe_allow_html=True,
    )
    with st.expander(f"{evidence.get('display_id')} · 原文、图示与检索上下文", expanded=False):
        st.markdown(
            f"**检索分值：** {format_score(evidence.get('score'))}  "
            f"**视觉状态：** {evidence.get('visual_status') or 'missing'}  "
            f"**Collection：** {evidence.get('collection') or '未记录'}"
        )
        image_path = str(evidence.get("image_path") or "")
        if image_path:
            resolved = resolve_project_path(image_path)
            if resolved and resolved.is_file():
                st.image(str(resolved), caption=f"{evidence.get('figure_number') or evidence.get('display_id')} · {location}")
            else:
                st.warning("图像文件不可用；证据记录已保留原始路径。")
                st.code(image_path, language="text")
        elif str(evidence.get("modality") or "").lower() in {"figure", "visual"}:
            st.markdown(
                '<div class="image-placeholder"><strong>图示文件未解析</strong><span>当前仅保留页面文字或图示元数据</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown("**证据原文**")
        st.write(evidence.get("content") or "未返回原文。")
        if evidence.get("metadata"):
            with st.expander("检索元数据", expanded=False):
                st.json(evidence["metadata"], expanded=False)
