"""Supervisor plan and dynamically selected Agent rendering."""

from __future__ import annotations

from typing import Any, Mapping

import streamlit as st

from .common import badge, esc, section_heading


def render_task_plan(result: Mapping[str, Any]) -> None:
    raw = result.get("raw_response", {})
    plan = raw.get("agent_plan", {}) if isinstance(raw, Mapping) else {}
    query_context = raw.get("query_context", {}) if isinstance(raw, Mapping) else {}
    tasks = list(result.get("task_plan") or [])
    agents = list(result.get("selected_agents") or [])
    missing = list(query_context.get("missing_slots") or []) if isinstance(query_context, Mapping) else []

    section_heading("Supervisor 任务计划", "PLAN")
    st.markdown(
        f"""
        <div class="plan-summary">
          <div><span>任务识别</span><strong>{esc(' + '.join(result.get('task_type') or ['UNKNOWN']))}</strong></div>
          <div><span>执行模式</span><strong>{esc(plan.get('execution_mode') or '未执行')}</strong></div>
          <div><span>专业 Agent</span><strong>{len(agents)}</strong></div>
          <div><span>缺失槽位</span><strong>{len(missing)}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if plan.get("need_clarification"):
        st.warning(str(plan.get("clarification_prompt") or query_context.get("clarify_question") or "需要补充设备信息。"))

    if not tasks:
        st.info("Supervisor 未返回可展示的结构化任务。")
    for index, task in enumerate(tasks, start=1):
        assigned = "、".join(task.get("assigned_agents") or []) or "待分配"
        modalities = " / ".join(task.get("required_modalities") or []) or "按任务判断"
        st.markdown(
            f"""
            <div class="task-row">
              <span class="task-index">{index:02d}</span>
              <div class="task-copy">
                <strong>{esc(task.get('title'))}</strong>
                <p>{esc(task.get('description'))}</p>
                <small>{esc(assigned)} · {esc(modalities)}</small>
              </div>
              {badge(str(task.get('status') or 'waiting'))}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_agent_flow(result: Mapping[str, Any]) -> None:
    agents = list(result.get("selected_agents") or [])
    section_heading("动态 Agent 协作", "AGENTS")
    if not agents:
        st.markdown(
            '<div class="agent-flow"><span class="flow-node flow-supervisor">Supervisor</span>'
            '<span class="flow-arrow">→</span><span class="flow-node flow-muted">澄清 / 未调用专业 Agent</span></div>',
            unsafe_allow_html=True,
        )
        return

    nodes = ['<span class="flow-node flow-supervisor">Supervisor</span>']
    for agent in agents:
        nodes.append('<span class="flow-arrow">→</span>')
        nodes.append(f'<span class="flow-node">{esc(agent.get("name"))}</span>')
    st.markdown(f'<div class="agent-flow">{"".join(nodes)}</div>', unsafe_allow_html=True)

    for agent in agents:
        tools = "、".join(agent.get("tools") or []) or "未记录"
        error_html = f'<p class="agent-error">{esc(agent.get("error"))}</p>' if agent.get("error") else ""
        st.markdown(
            f"""
            <div class="agent-card agent-{esc(agent.get('status'))}">
              <div class="agent-card-head">
                <div><strong>{esc(agent.get('name'))}</strong><span>{esc(agent.get('task') or '任务未描述')}</span></div>
                {badge(str(agent.get('status') or 'waiting'))}
              </div>
              <div class="agent-metrics">
                <span>工具 <b>{esc(tools)}</b></span>
                <span>证据 <b>{int(agent.get('evidence_count') or 0)} 条</b></span>
                <span>耗时 <b>{int(agent.get('elapsed_ms') or 0)} ms</b></span>
                <span>置信度 <b>{esc(agent.get('confidence'))}</b></span>
              </div>
              {error_html}
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander(f"{agent.get('name')} · 结论与调用记录", expanded=False):
            st.write(agent.get("conclusion") or "未返回结论文本。")
            if agent.get("observations"):
                st.dataframe(agent["observations"], width="stretch", hide_index=True)
            if agent.get("claims"):
                st.json(agent["claims"], expanded=False)
