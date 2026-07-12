#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentStatus
from ..tools.tool_registry import ToolRegistry
from ..evidence.evidence_ranker import rank_evidence
from ..evidence.fact_extractors import extract_parameter_facts
from ..evidence.model_identity import extract_model_identity
from .base_agent import BaseAgent


class ParameterAgent(BaseAgent):
    agent_name = "Parameter Agent"
    role_description = "Specialist for module parameters, order numbers, voltage, current, power and table evidence."
    tool_names = ["search_table", "search_text"]
    default_claim_type = "parameter"

    def execute(self, task, registry: ToolRegistry, evidence_pool: SharedEvidencePool):
        query = self._join_query(task)
        combined = registry.search_table(query, top_k=8) + registry.search_text(query, top_k=8)
        evidences = rank_evidence(combined, query=query, top_k=12)
        if not evidences:
            return self._abstain(task, "No parameter table or text evidence was found.")
        extracted = [(item, extract_parameter_facts(item.text, "电源电压允许范围")) for item in evidences]
        selected = next(((item, facts) for item, facts in extracted if facts.complete), None)
        if not selected:
            return self._abstain(task, "No single evidence item contained a complete supported parameter range.")
        top, facts = selected
        model = extract_model_identity(task.input_slots.get("module_model", "") or task.query).normalized_model or top.module_model
        number = lambda value: f"{value:g}"
        claim = (
            f"{model or '该模块'} 的电源电压允许范围为：静态 {number(facts.static_lower)}～{number(facts.static_upper)} V DC，"
            f"动态 {number(facts.dynamic_lower)}～{number(facts.dynamic_upper)} V DC。"
        )
        answer = claim
        return self._finish_with_evidence(
            task,
            [top],
            evidence_pool,
            answer_fragment=answer,
            claim=claim,
            confidence="HIGH" if top.model_match_level in {"exact_model", "exact_order_number"} else "MEDIUM",
            status=AgentStatus.ANSWERED.value,
            claim_type="parameter",
            claim_metadata={
                "parameter_name": facts.parameter_name,
                "rated_values": facts.rated_values,
                "static_lower": facts.static_lower,
                "dynamic_lower": facts.dynamic_lower,
                "static_upper": facts.static_upper,
                "dynamic_upper": facts.dynamic_upper,
                "unit": facts.unit,
                "condition": facts.condition,
                "source_page": top.page,
                "source_section": top.section,
                "evidence_span": facts.evidence_span,
                "fact_type": "parameter_range",
                "inference_level": "direct",
            },
        )
