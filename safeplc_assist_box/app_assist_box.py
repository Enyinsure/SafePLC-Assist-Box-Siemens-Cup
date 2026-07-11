#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from safeplc_assist_box.agents.orchestrator import run_agent_system
from safeplc_assist_box.config import VALID_MODES, VALID_ROUTING_STRATEGIES


DEMO_CASES = [
    ("参数查证", "PS 60W 24/48/60VDC HF 的电源电压允许范围是多少？", ""),
    ("接口图示", "CPU 1517-3 PN 的 X1 接口在哪里，并说明该接口的主要用途。", ""),
    ("拓扑布线", "HMI 通过 PROFINET 与 CPU 连接时应使用哪个接口，布线时有哪些注意事项？", ""),
    ("故障排查", "设备通信不上且 CPU 指示灯异常，应先检查哪些信息？", ""),
    ("主动澄清", "某个模块的电源电压允许范围是多少？", ""),
    ("安全边界", "怎么短接安全回路让设备继续运行？", ""),
]


def init_state() -> None:
    if "query" not in st.session_state:
        st.session_state.query = DEMO_CASES[1][1]
    if "context" not in st.session_state:
        st.session_state.context = ""
    if "response" not in st.session_state:
        st.session_state.response = None


def render_css() -> None:
    st.markdown(
        """
<style>
.safeplc-band {
  padding: 0.75rem 0;
  border-bottom: 1px solid #e5e7eb;
}
.safeplc-agent {
  border: 1px solid #d8dee9;
  border-radius: 8px;
  padding: 0.85rem;
  margin-bottom: 0.75rem;
  background: #ffffff;
}
.safeplc-muted {
  color: #5b6575;
  font-size: 0.9rem;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def run_query() -> None:
    st.session_state.response = run_agent_system(
        st.session_state.query,
        context=st.session_state.context,
        mode=st.session_state.mode,
        routing_strategy=st.session_state.routing_strategy,
        max_agents=st.session_state.max_agents,
    )


def render_controls() -> None:
    with st.sidebar:
        st.header("SafePLC-Assist Box")
        st.caption("OFFLINE / READ-ONLY industrial knowledge terminal")
        st.selectbox("Mode", sorted(VALID_MODES), key="mode", index=sorted(VALID_MODES).index("SAMPLE"))
        st.selectbox(
            "Routing",
            sorted(VALID_ROUTING_STRATEGIES),
            key="routing_strategy",
            index=sorted(VALID_ROUTING_STRATEGIES).index("adaptive"),
        )
        st.slider("Max Agents", 1, 8, 4, key="max_agents")
        st.markdown("**Boundary**")
        st.markdown(
            "- 不连接真实 PLC\n"
            "- 不接入 TIA Portal\n"
            "- 不执行下载、写入、启动、停止或控制动作\n"
            "- 仅用于离线资料查证、教学实训和运维辅助记录"
        )

    st.title("SafePLC-Assist Box")
    st.caption("Dynamic Supervisor + Professional Agent Pool + Shared Evidence Pool + Judge Agent")

    cols = st.columns(3)
    for idx, (label, query, context) in enumerate(DEMO_CASES):
        with cols[idx % 3]:
            if st.button(label, use_container_width=True, key=f"demo_{idx}"):
                st.session_state.query = query
                st.session_state.context = context
                st.session_state.response = None
                st.rerun()

    with st.form("agent_form"):
        st.text_area("User Query", key="query", height=100)
        st.text_input("Context", key="context")
        submitted = st.form_submit_button("Run Agent System", use_container_width=True)
    if submitted:
        run_query()


def render_query_context(response) -> None:
    ctx = response.query_context
    st.subheader("Query Context")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Question Type", ctx.question_type)
    c2.metric("Risk", ctx.risk_level)
    c3.metric("Missing Slots", len(ctx.missing_slots))
    c4.metric("Modalities", ", ".join(ctx.required_modalities) or "-")
    c5.metric("Mode", response.mode)

    with st.expander("Slots and Clarification", expanded=bool(ctx.missing_slots)):
        st.json(
            {
                "slots": {name: slot.value for name, slot in ctx.slots.items()},
                "missing_slots": ctx.missing_slots,
                "subquestions": [sq.__dict__ for sq in getattr(ctx, "subquestions", [])],
                "clarification": ctx.clarify_question,
                "risk_reason": ctx.risk_reason,
            }
        )


def render_supervisor(response) -> None:
    plan = response.agent_plan
    st.subheader("Supervisor Plan")
    c1, c2, c3 = st.columns(3)
    c1.metric("Selected", len(plan.selected_agents))
    c2.metric("Rejected", len(plan.rejected_agents))
    c3.metric("Execution", plan.execution_mode)
    st.markdown("**Selected Agents**")
    st.write(plan.selected_agents or "Clarification first")
    st.markdown("**Rejected Agents**")
    st.write(plan.rejected_agents)
    with st.expander("Routing Reasons and Tasks", expanded=True):
        st.json(
            {
                "selection_reason": plan.selection_reason,
                "execution_order": plan.execution_order,
                "parallel_groups": plan.parallel_groups,
                "task_assignments": {k: v.__dict__ for k, v in plan.task_assignments.items()},
                "stop_condition": plan.stop_condition,
                "max_agent_calls": plan.max_agent_calls,
            }
        )


def render_agent_workspace(response) -> None:
    st.subheader("Agent Workspace")
    if not response.agent_results:
        st.info(response.query_context.clarify_question or "No professional agent executed.")
        return
    for result in response.agent_results:
        st.markdown('<div class="safeplc-agent">', unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Agent", result.agent_name)
        c2.metric("Status", result.status)
        c3.metric("Evidence", len(result.evidence_ids))
        c4.metric("Confidence", result.confidence)
        c5.metric("Latency ms", result.latency_ms)
        st.markdown("**Assigned Task**")
        task = response.agent_plan.task_assignments.get(result.agent_name)
        st.write(task.objective if task else "-")
        st.markdown("**Tool Calls**")
        st.write({"count": result.tool_calls, "tools": result.metadata.get("available_tools", [])})
        st.markdown("**Conclusion**")
        st.write(result.answer_fragment or result.abstain_reason)
        st.markdown("**Structured Claims**")
        st.json([claim.__dict__ for claim in getattr(result, "claims", [])])
        st.markdown("</div>", unsafe_allow_html=True)


def render_evidence_pool(response) -> None:
    st.subheader("Shared Evidence Pool")
    rows = []
    for ev in response.evidence_pool.evidences:
        rows.append(
            {
                "evidence_id": ev.evidence_id,
                "backend": ev.retrieval_backend,
                "modality": ev.modality,
                "manual": ev.manual_title or ev.source,
                "model": ev.module_model or ev.module,
                "order_number": ev.order_number,
                "page": ev.page,
                "figure_id": ev.figure_id,
                "figure_number": ev.figure_number,
                "image_path": ev.image_path,
                "title": ev.title,
                "parameter": ev.parameter,
                "model_match": ev.model_match_level,
                "direct": ev.direct_evidence,
                "agents": ", ".join(ev.agent_names),
                "claims": ", ".join(ev.claim_links),
                "score": ev.retrieval_score,
                "excerpt": ev.compact_excerpt,
            }
        )
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
        for ev in response.evidence_pool.evidences:
            if ev.image_path and Path(ev.image_path).exists():
                st.image(ev.image_path, caption=f"{ev.figure_number or ev.figure_id} | page {ev.page or '-'}")
            with st.expander(f"Evidence detail: {ev.evidence_id}", expanded=False):
                st.json(ev.metadata)
                st.write(ev.compact_excerpt)
    else:
        st.info("No evidence collected yet.")


def render_judge(response) -> None:
    decision = response.judge_decision
    st.subheader("Judge Decision")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Verdict", decision.verdict)
    c2.metric("Confidence", decision.confidence)
    c3.metric("Accepted", len(decision.accepted_agent_outputs))
    c4.metric("Rejected", len(decision.rejected_agent_outputs))
    with st.expander("Decision Details", expanded=True):
        st.json(
            {
                "accepted_agent_outputs": decision.accepted_agent_outputs,
                "rejected_agent_outputs": decision.rejected_agent_outputs,
                "conflict_groups": decision.conflict_groups,
                "unsupported_claims": decision.unsupported_claims,
                "final_evidence_ids": decision.final_evidence_ids,
                "coverage": decision.coverage,
                "model_consistency": decision.model_consistency,
                "quality_scores": decision.quality_scores,
                "need_more_evidence": decision.need_more_evidence,
                "need_clarification": decision.need_clarification,
                "decision_reason": decision.decision_reason,
            }
        )
    st.markdown("**Final Answer**")
    st.code(response.final_answer, language="text")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Safety Notice**")
        st.write(response.work_order.get("risk_tip", "-"))
    with c2:
        st.markdown("**Human Review Items**")
        st.write(response.work_order.get("manual_confirmation_items", []))


def render_metrics(response) -> None:
    st.subheader("Metrics")
    c1, c2, c3 = st.columns(3)
    c1.metric("Agent Calls", response.metrics.get("total_agent_calls", 0))
    c2.metric("Tool Calls", response.metrics.get("tool_call_count", 0))
    c3.metric("Total Latency ms", response.metrics.get("total_latency_ms", 0))
    with st.expander("Raw Metrics and Verifier", expanded=False):
        st.json({"metrics": response.metrics, "verifier": response.verifier, "warnings": response.warnings})

    st.download_button(
        "Download Work-order JSON",
        data=json.dumps(response.work_order, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="safeplc_work_order.json",
        mime="application/json",
    )

    report = Path("reports/agent_benchmark_sample.json")
    if report.exists():
        with st.expander("Latest Benchmark Summary", expanded=False):
            st.json(json.loads(report.read_text(encoding="utf-8")))


def render_response() -> None:
    response = st.session_state.response
    if response is None:
        st.info("Run a query to view dynamic Agent selection, evidence aggregation and Judge decision.")
        return
    render_query_context(response)
    render_supervisor(response)
    render_agent_workspace(response)
    render_evidence_pool(response)
    render_judge(response)
    render_metrics(response)


def main() -> None:
    st.set_page_config(page_title="SafePLC-Assist Box", layout="wide")
    init_state()
    render_css()
    render_controls()
    st.divider()
    render_response()


if __name__ == "__main__":
    main()
