#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Dict, List, Tuple

from ..schemas import AgentPlan, AgentTask, ExecutionMode, QueryContext


PROFESSIONAL_AGENTS = [
    "Parameter Agent",
    "Figure Agent",
    "Wiring Agent",
    "Topology Agent",
    "Troubleshooting Agent",
    "EMC Agent",
    "Safety Boundary Agent",
    "Work-order Agent",
]


AGENT_TOOLS = {
    "Parameter Agent": ["search_table", "search_text"],
    "Figure Agent": ["search_figure", "search_hybrid"],
    "Wiring Agent": ["search_text", "search_table", "search_figure"],
    "Topology Agent": ["search_hybrid", "search_text", "search_figure"],
    "Troubleshooting Agent": ["search_text", "search_table"],
    "EMC Agent": ["search_text", "search_hybrid"],
    "Safety Boundary Agent": ["search_text"],
    "Work-order Agent": ["structured_export"],
}


class SupervisorAgent:
    role_description = "Dynamic supervisor that plans specialist agents from query context and subquestions."

    def plan(
        self,
        query_context: QueryContext,
        routing_strategy: str = "adaptive",
        max_agents: int = 4,
    ) -> AgentPlan:
        if query_context.is_dangerous_operation:
            selected = ["Safety Boundary Agent"]
            return self._build_plan(
                query_context,
                selected,
                routing_strategy,
                max_agent_calls=1,
                execution_mode=ExecutionMode.SINGLE.value,
                reason_override={"Safety Boundary Agent": "High-risk industrial operation: refuse executable steps."},
            )

        if query_context.missing_slots:
            return self._clarify_plan(query_context, routing_strategy, max_agents)

        scores = self._score_agents(query_context)
        ordered = [name for name, score in sorted(scores.items(), key=lambda x: x[1], reverse=True) if score > 0]
        if not ordered:
            ordered = ["Troubleshooting Agent"]

        if routing_strategy == "all_agents":
            selected = [a for a in PROFESSIONAL_AGENTS if a != "Work-order Agent"]
            if query_context.expected_output_type == "work_order":
                selected.append("Work-order Agent")
            max_calls = len(selected)
        elif routing_strategy == "static":
            static_map = {
                "PARAMETER": "Parameter Agent",
                "FIGURE": "Figure Agent",
                "WIRING": "Wiring Agent",
                "TOPOLOGY": "Topology Agent",
                "TROUBLESHOOTING": "Troubleshooting Agent",
                "EMC": "EMC Agent",
                "WORK_ORDER": "Work-order Agent",
            }
            selected = [static_map.get(query_context.question_type, "Troubleshooting Agent")]
            max_calls = 1
        elif routing_strategy == "single_best":
            selected = ordered[:1]
            max_calls = 1
        elif routing_strategy == "top_k":
            selected = ordered[: max(1, min(max_agents, len(ordered)))]
            max_calls = max_agents
        else:
            selected = self._adaptive_select(query_context, ordered, scores, max_agents)
            max_calls = max_agents

        if query_context.expected_output_type == "work_order" and "Work-order Agent" not in selected:
            selected = selected[: max(0, max_calls - 1)] + ["Work-order Agent"]

        execution_mode = self._execution_mode(selected, query_context)
        return self._build_plan(
            query_context,
            selected,
            routing_strategy,
            max_agent_calls=max_calls,
            execution_mode=execution_mode,
            scores=scores,
        )

    def _clarify_plan(self, query_context: QueryContext, routing_strategy: str, max_agents: int) -> AgentPlan:
        return AgentPlan(
            selected_agents=[],
            rejected_agents=list(PROFESSIONAL_AGENTS),
            selection_reason={"Clarification": "Required slots are missing; no professional agent is called yet."},
            execution_mode=ExecutionMode.CLARIFY.value,
            task_assignments={},
            expected_evidence_types=query_context.required_modalities,
            stop_condition="wait_for_user_clarification",
            max_agent_calls=max_agents,
            routing_strategy=routing_strategy,
            execution_order=[],
            parallel_groups=[],
            need_clarification=True,
            clarification_prompt=query_context.clarify_question,
            metadata={"missing_slots": list(query_context.missing_slots)},
        )

    def _score_agents(self, ctx: QueryContext) -> Dict[str, float]:
        scores = {name: 0.0 for name in PROFESSIONAL_AGENTS}
        qtype = ctx.question_type
        text = ctx.normalized_query.lower()

        qtype_boost = {
            "PARAMETER": {"Parameter Agent": 6.0},
            "FIGURE": {"Figure Agent": 6.0, "Topology Agent": 1.2},
            "WIRING": {"Wiring Agent": 6.0, "EMC Agent": 2.0, "Figure Agent": 1.5},
            "TOPOLOGY": {"Topology Agent": 6.0, "Figure Agent": 2.5 if "x1" in text else 0.5, "Wiring Agent": 1.0},
            "TROUBLESHOOTING": {"Troubleshooting Agent": 6.0, "Figure Agent": 1.5, "Parameter Agent": 1.0},
            "EMC": {"EMC Agent": 6.0, "Wiring Agent": 1.5},
            "WORK_ORDER": {"Work-order Agent": 5.0, "Troubleshooting Agent": 1.0},
            "GENERAL_INDUSTRIAL_QA": {"Parameter Agent": 1.0, "Troubleshooting Agent": 1.0},
        }
        for agent, value in qtype_boost.get(qtype, {}).items():
            scores[agent] += value

        keyword_boosts: List[Tuple[List[str], str, float]] = [
            (["电压", "电流", "功率", "温度", "订货号", "参数", "voltage"], "Parameter Agent", 1.5),
            (["图", "前面板", "接口", "x1", "x2", "where", "哪里"], "Figure Agent", 1.4),
            (["接线", "端子", "线缆", "wiring"], "Wiring Agent", 1.5),
            (["profinet", "hmi", "拓扑", "环网"], "Topology Agent", 1.5),
            (["故障", "报警", "指示灯", "通信不上", "排查"], "Troubleshooting Agent", 1.5),
            (["emc", "电磁兼容", "接地", "屏蔽"], "EMC Agent", 1.5),
        ]
        for words, agent, boost in keyword_boosts:
            if any(w.lower() in text for w in words):
                scores[agent] += boost

        for subq in ctx.subquestions:
            for agent in subq.expected_agents:
                if agent in scores:
                    scores[agent] += 2.0

        modalities = set(ctx.required_modalities)
        if "table" in modalities:
            scores["Parameter Agent"] += 0.8
        if "figure" in modalities:
            scores["Figure Agent"] += 0.8
            scores["Topology Agent"] += 0.4
        if ctx.risk_level == "CAUTION":
            scores["Safety Boundary Agent"] += 0.5
        return scores

    def _adaptive_select(
        self,
        ctx: QueryContext,
        ordered: List[str],
        scores: Dict[str, float],
        max_agents: int,
    ) -> List[str]:
        selected: List[str] = []
        if ctx.question_type == "EMC":
            return ["EMC Agent"]
        for subq in ctx.subquestions:
            for agent in subq.expected_agents:
                if agent in ordered and agent not in selected and scores.get(agent, 0) > 0:
                    selected.append(agent)
                if len(selected) >= max_agents:
                    return selected[:max_agents]
        if not selected:
            selected.append(ordered[0])
        if any(subq.expected_agents for subq in ctx.subquestions):
            return selected[:max_agents]
        multi_signal = len(ctx.subquestions) > 1 or any(token in ctx.normalized_query for token in ["并", "同时", "以及", "+", "和"])
        if multi_signal:
            for agent in ordered:
                if len(selected) >= max_agents:
                    break
                if agent not in selected and scores[agent] >= 1.5:
                    selected.append(agent)
        return selected[:max_agents]

    def _execution_mode(self, selected: List[str], ctx: QueryContext) -> str:
        if len(selected) <= 1:
            return ExecutionMode.SINGLE.value
        if "Work-order Agent" in selected:
            return ExecutionMode.SERIAL.value
        return ExecutionMode.PARALLEL.value

    def _build_plan(
        self,
        query_context: QueryContext,
        selected: List[str],
        routing_strategy: str,
        max_agent_calls: int,
        execution_mode: str,
        reason_override: Dict[str, str] | None = None,
        scores: Dict[str, float] | None = None,
    ) -> AgentPlan:
        reason_override = reason_override or {}
        scores = scores or self._score_agents(query_context)
        rejected = [a for a in PROFESSIONAL_AGENTS if a not in selected]
        tasks: Dict[str, AgentTask] = {}
        slot_values = query_context.slot_values()
        for idx, agent in enumerate(selected, start=1):
            objective = self._objective_for(agent, query_context)
            assigned = [sq for sq in query_context.subquestions if not sq.expected_agents or agent in sq.expected_agents]
            subquestion_ids = [sq.subquestion_id for sq in assigned]
            task_query = "\n".join(sq.text for sq in assigned).strip() or query_context.original_query
            required_evidence = list(dict.fromkeys(item for sq in assigned for item in sq.required_modalities)) or query_context.required_modalities
            tasks[agent] = AgentTask(
                task_id=f"task_{idx:02d}_{agent.lower().replace(' ', '_').replace('-', '_')}",
                agent_name=agent,
                role=agent,
                query=task_query,
                context=query_context.context,
                objective=objective,
                input_slots=slot_values,
                required_evidence_types=required_evidence,
                tool_names=AGENT_TOOLS.get(agent, []),
                constraints=[
                    "Only cite evidence returned by ToolRegistry.",
                    "Abstain when no evidence supports the task.",
                    "Do not control real PLC devices.",
                    "Return structured claims, not raw page OCR.",
                ],
                subquestion_ids=subquestion_ids,
                metadata={"original_query": query_context.original_query},
            )
        reasons = {
            agent: reason_override.get(
                agent,
                f"score={scores.get(agent, 0):.2f}; question_type={query_context.question_type}; subquestions={len(query_context.subquestions)}",
            )
            for agent in selected
        }
        return AgentPlan(
            selected_agents=selected,
            rejected_agents=rejected,
            selection_reason=reasons,
            execution_mode=execution_mode,
            task_assignments=tasks,
            expected_evidence_types=query_context.required_modalities,
            stop_condition="max_agent_calls_or_sufficient_evidence",
            max_agent_calls=max_agent_calls,
            routing_strategy=routing_strategy,
            execution_order=list(selected),
            parallel_groups=[list(selected)] if execution_mode == ExecutionMode.PARALLEL.value else [[a] for a in selected],
            scores=scores,
            metadata={"subquestions": [sq.subquestion_id for sq in query_context.subquestions]},
        )

    def _objective_for(self, agent: str, ctx: QueryContext) -> str:
        objectives = {
            "Parameter Agent": "Verify model/order number, parameter name, numeric value and unit.",
            "Figure Agent": "Locate interface, figure number, page, marker and image/page-text evidence.",
            "Wiring Agent": "Extract directly evidenced terminal and wiring requirements.",
            "Topology Agent": "Verify PROFINET/HMI/CPU/IO relationship and connection guidance.",
            "Troubleshooting Agent": "Extract directly supported LED checks for the reported symptom.",
            "EMC Agent": "Verify grounding, shielding, cabling and installation environment requirements.",
            "Safety Boundary Agent": "Refuse dangerous industrial operation steps and provide safe alternatives.",
            "Work-order Agent": "Export the final verified result as structured maintenance assistance record.",
        }
        return objectives.get(agent, "Complete evidence-grounded industrial knowledge task.")
