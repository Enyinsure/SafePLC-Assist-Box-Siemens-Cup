#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import copy
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List

from ..config import SafePLCConfig
from ..evidence.answer_evidence_verifier import verify_answer_evidence
from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentPlan, AgentResult, SafePLCResponse
from ..tools.tool_registry import ToolRegistry
from .context_analyzer import ContextAnalyzer
from .emc_agent import EMCAgent
from .figure_agent import FigureAgent
from .judge_agent import JudgeAgent
from .parameter_agent import ParameterAgent
from .safety_boundary_agent import SafetyBoundaryAgent
from .supervisor_agent import SupervisorAgent
from .topology_agent import TopologyAgent
from .troubleshooting_agent import TroubleshootingAgent
from .wiring_agent import WiringAgent
from .work_order_agent import WorkOrderAgent


AGENT_FACTORY = {
    "Parameter Agent": ParameterAgent,
    "Figure Agent": FigureAgent,
    "Wiring Agent": WiringAgent,
    "Topology Agent": TopologyAgent,
    "Troubleshooting Agent": TroubleshootingAgent,
    "EMC Agent": EMCAgent,
    "Safety Boundary Agent": SafetyBoundaryAgent,
    "Work-order Agent": WorkOrderAgent,
}


def run_agent_system(
    query: str,
    context: str = "",
    mode: str | None = None,
    routing_strategy: str = "adaptive",
    max_agents: int = 4,
) -> SafePLCResponse:
    started = time.perf_counter()
    config = SafePLCConfig.from_env(
        mode=mode,
        routing_strategy=routing_strategy,
        max_agents=max_agents,
    )
    registry = ToolRegistry(config)
    evidence_pool = SharedEvidencePool()

    query_context = ContextAnalyzer().analyze(query, context)
    supervisor = SupervisorAgent()
    plan = supervisor.plan(
        query_context,
        routing_strategy=config.routing_strategy,
        max_agents=config.max_agents,
    )

    results: List[AgentResult] = []
    early_stop_reason = ""

    if not plan.need_clarification:
        results = _execute_plan(plan, registry, evidence_pool)
        if (
            config.routing_strategy == "adaptive"
            and not any(r.evidence_ids for r in results)
            and len(results) < plan.max_agent_calls
        ):
            added = _run_adaptive_fallback(plan, registry, evidence_pool, results)
            if added:
                results.extend(added)
            else:
                early_stop_reason = "no_adaptive_fallback_available"
        elif config.routing_strategy == "adaptive":
            early_stop_reason = "sufficient_evidence_after_adaptive_selection"

    pool_schema = evidence_pool.to_schema()
    judge_decision = JudgeAgent().decide(query_context, results, pool_schema)
    verifier = verify_answer_evidence(
        judge_decision.final_answer,
        judge_decision,
        pool_schema.evidences,
    )
    work_order = _build_work_order(query, context, judge_decision.final_answer, pool_schema, query_context)
    total_latency = int((time.perf_counter() - started) * 1000)
    agent_latency = {result.agent_name: result.latency_ms for result in results}

    metrics = {
        "selected_agents": list(plan.selected_agents),
        "execution_order": [r.agent_name for r in results],
        "parallel_groups": list(plan.parallel_groups),
        "total_agent_calls": len(results),
        "total_tool_calls": registry.tool_call_count,
        "tool_call_count": registry.tool_call_count,
        "total_latency_ms": total_latency,
        "agent_latency_ms": agent_latency,
        "routing_reason": dict(plan.selection_reason),
        "early_stop_reason": early_stop_reason,
        "mode": config.mode,
        "routing_strategy": config.routing_strategy,
    }

    warnings = []
    if config.mode == "FULL" and not config.full_assets_available():
        missing_assets = []
        if not config.chunks_jsonl:
            missing_assets.append("SAFEPLC_CHUNKS_JSONL")
        if not config.pages_jsonl:
            missing_assets.append("SAFEPLC_PAGES_JSONL")
        warnings.append(
            "FULL mode requested but required JSONL assets are missing: "
            + ", ".join(missing_assets or ["configured JSONL files do not exist"])
            + "; ToolRegistry used SAMPLE evidence for this local run."
        )

    if plan.need_clarification:
        action = "CLARIFY"
    elif any(result.status == "REFUSE" for result in results):
        action = "REFUSE"
    else:
        action = "ANSWER"
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return SafePLCResponse(
        query=query,
        context=context,
        mode=config.mode,
        query_context=query_context,
        agent_plan=plan,
        agent_results=results,
        evidence_pool=pool_schema,
        judge_decision=judge_decision,
        verifier=verifier,
        final_answer=judge_decision.final_answer,
        question_type=query_context.question_type,
        extracted_slots=query_context.slot_values(),
        missing_slots=list(query_context.missing_slots),
        operation_risk_level=query_context.risk_level,
        action=action,
        routing_strategy=config.routing_strategy,
        selected_agents=list(plan.selected_agents),
        execution_order=[r.agent_name for r in results],
        evidence_items=list(pool_schema.evidences),
        supported_claims=list(judge_decision.supported_claims),
        unsupported_claims=list(judge_decision.unsupported_claims),
        conflicting_claims=list(judge_decision.conflicting_claims),
        verdict=judge_decision.verdict,
        confidence=judge_decision.confidence,
        total_agent_calls=len(results),
        total_tool_calls=registry.tool_call_count,
        total_latency_ms=total_latency,
        generated_at=generated_at,
        version="agent_first_v1",
        work_order=work_order,
        metrics=metrics,
        warnings=warnings,
    )


def _execute_plan(
    plan: AgentPlan,
    registry: ToolRegistry,
    evidence_pool: SharedEvidencePool,
) -> List[AgentResult]:
    if not plan.selected_agents:
        return []
    if plan.execution_mode == "parallel" and len(plan.selected_agents) > 1:
        return _execute_parallel(plan, registry, evidence_pool)
    results: List[AgentResult] = []
    for agent_name in plan.execution_order:
        if len(results) >= plan.max_agent_calls:
            break
        result = _execute_agent(agent_name, plan, registry, evidence_pool)
        if result:
            results.append(result)
    return results


def _execute_parallel(
    plan: AgentPlan,
    registry: ToolRegistry,
    evidence_pool: SharedEvidencePool,
) -> List[AgentResult]:
    results_by_name: Dict[str, AgentResult] = {}
    groups = plan.parallel_groups or [plan.selected_agents]
    for group in groups:
        with ThreadPoolExecutor(max_workers=max(1, min(len(group), plan.max_agent_calls))) as executor:
            futures = {
                executor.submit(_execute_agent, agent_name, plan, registry, evidence_pool): agent_name
                for agent_name in group[: plan.max_agent_calls]
            }
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results_by_name[result.agent_name] = result
    return [results_by_name[name] for name in plan.execution_order if name in results_by_name]


def _execute_agent(
    agent_name: str,
    plan: AgentPlan,
    registry: ToolRegistry,
    evidence_pool: SharedEvidencePool,
) -> AgentResult | None:
    cls = AGENT_FACTORY.get(agent_name)
    task = plan.task_assignments.get(agent_name)
    if not cls or not task:
        return None
    return cls().run(task, registry, evidence_pool)


def _run_adaptive_fallback(
    plan: AgentPlan,
    registry: ToolRegistry,
    evidence_pool: SharedEvidencePool,
    existing: List[AgentResult],
) -> List[AgentResult]:
    already = {r.agent_name for r in existing}
    ordered_rejected = sorted(
        plan.rejected_agents,
        key=lambda name: plan.scores.get(name, 0.0),
        reverse=True,
    )
    added: List[AgentResult] = []
    for agent_name in ordered_rejected:
        if len(existing) + len(added) >= plan.max_agent_calls:
            break
        if agent_name in already or plan.scores.get(agent_name, 0.0) <= 0:
            continue
        if agent_name == "Work-order Agent":
            continue
        task = next(iter(plan.task_assignments.values()), None)
        if not task:
            continue
        fallback_task = copy.deepcopy(task)
        fallback_task.agent_name = agent_name
        fallback_task.task_id = f"adaptive_{agent_name.lower().replace(' ', '_').replace('-', '_')}"
        fallback_task.tool_names = []
        temp_plan = AgentPlan(
            selected_agents=[agent_name],
            rejected_agents=[],
            selection_reason={agent_name: "adaptive fallback after insufficient evidence"},
            execution_mode="single",
            task_assignments={agent_name: fallback_task},
            expected_evidence_types=plan.expected_evidence_types,
            stop_condition=plan.stop_condition,
            max_agent_calls=1,
            routing_strategy=plan.routing_strategy,
            execution_order=[agent_name],
        )
        result = _execute_agent(agent_name, temp_plan, registry, evidence_pool)
        if result:
            added.append(result)
    return added


def _build_work_order(query, context, final_answer, pool_schema, query_context) -> Dict[str, object]:
    return {
        "user_query": query,
        "context": context,
        "device_info": query_context.slot_values(),
        "phenomenon": query_context.slots.get("alarm_code").value if query_context.slots.get("alarm_code") else "",
        "verified_evidence": [ev.evidence_id for ev in pool_schema.evidences],
        "risk_tip": query_context.risk_reason,
        "suggested_checks": [
            "核对型号、订货号、接口名和页码。",
            "将资料查证结果交由具备资质人员复核。",
        ],
        "manual_confirmation_items": list(query_context.missing_slots),
        "final_answer": final_answer,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SafePLC-Assist Box agent system.")
    parser.add_argument("query")
    parser.add_argument("--context", default="")
    parser.add_argument("--mode", default=None)
    parser.add_argument("--routing-strategy", default="adaptive")
    parser.add_argument("--max-agents", type=int, default=4)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    response = run_agent_system(
        args.query,
        context=args.context,
        mode=args.mode,
        routing_strategy=args.routing_strategy,
        max_agents=args.max_agents,
    )
    if args.json:
        print(json.dumps(response.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(response.final_answer)


if __name__ == "__main__":
    main()
