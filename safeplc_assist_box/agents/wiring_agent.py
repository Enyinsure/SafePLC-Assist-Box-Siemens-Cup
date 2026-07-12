#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentResult, AgentStatus
from ..tools.tool_registry import ToolRegistry
from .base_agent import BaseAgent
from ..evidence.evidence_ranker import rank_evidence
from ..evidence.fact_extractors import extract_wiring_facts, wiring_fact_score


class WiringAgent(BaseAgent):
    agent_name = "Wiring Agent"
    role_description = "Specialist for terminal definitions, wiring constraints and installation safety notes."
    tool_names = ["search_text", "search_table", "search_figure"]
    default_claim_type = "connection"

    def execute(self, task, registry: ToolRegistry, evidence_pool: SharedEvidencePool):
        query = self._join_query(task)
        risky_terms = ["短接", "绕过", "带电", "force output", "强制输出", "bypass"]
        if any(term.lower() in query.lower() for term in risky_terms):
            boundary = registry.search_text("OFFLINE READ-ONLY industrial operation boundary", top_k=1)
            ids = evidence_pool.add_many(boundary, self.agent_name, claim="wiring_refusal")
            return AgentResult(
                agent_name=self.agent_name,
                task_id=task.task_id,
                status=AgentStatus.REFUSE.value,
                answer_fragment=(
                    "Refused: wiring questions that involve bypassing protection, live wiring or forced output "
                    "must be handled by stop, isolation and qualified review only."
                ),
                evidence_ids=ids,
                confidence="HIGH" if ids else "NOT_AVAILABLE",
                abstain_reason="" if ids else "No safety boundary evidence was found.",
            )
        candidates = registry.search_text(query, top_k=8) + registry.search_table(query, top_k=8)
        ranked = rank_evidence(candidates, query=query, top_k=12)
        scored = self._score_candidates(ranked, query)
        if not scored:
            scored = self._score_candidates(registry.search_figure(query, top_k=5), query)
        if not scored:
            return self._abstain(task, "No wiring or terminal evidence was found.")
        general_query = self._is_general_query(query)
        eligible = [item for item in scored if not (general_query and (item[3] or item[4]))]
        if not eligible:
            top = scored[0][1]
            ids = evidence_pool.add_many([top], self.agent_name, claim="scope_clarification")
            return AgentResult(
                agent_name=self.agent_name,
                task_id=task.task_id,
                status=AgentStatus.NEED_CLARIFICATION.value,
                answer_fragment="接线要求与具体模块和前连接器有关，请提供模块型号或订货号。",
                evidence_ids=ids,
                confidence="NOT_AVAILABLE",
                abstain_reason="Only module-specific or S7-1500R/H wiring evidence was found for a general query.",
            )
        _, top, facts, _, _ = eligible[0]
        general = self._is_system_level(top)
        claim = "；".join(facts[:4]) + "。"
        answer = f"{claim} Evidence: {top.manual_title or top.source}, page {top.page or '-'}."
        return self._finish_with_evidence(
            task,
            [top],
            evidence_pool,
            answer_fragment=answer,
            claim=claim,
            confidence="MEDIUM",
            status=AgentStatus.ANSWERED.value,
            claim_type="connection",
            claim_metadata={
                "terminal": top.metadata.get("terminal", ""),
                "signal": top.metadata.get("signal", ""),
                "voltage": top.metadata.get("voltage", ""),
                "polarity": top.metadata.get("polarity", ""),
                "connection_scope": top.module_model or top.device_family,
                "general_guidance": general,
                "evidence_span": "；".join(facts),
                "fact_type": "wiring_requirement",
                "source_page": top.page,
                "source_section": top.section,
                "inference_level": "general_guidance" if general else "direct",
                "wiring_fact_score": eligible[0][0],
            },
        )

    def _score_candidates(self, candidates, query):
        general_query = self._is_general_query(query)
        scored = []
        for item in candidates:
            facts = extract_wiring_facts(item.text)
            if not facts:
                continue
            rh_scope = self._is_rh_scope(item)
            specific_module = self._is_specific_module(item)
            score = wiring_fact_score(
                item.text,
                facts,
                system_level=self._is_system_level(item),
                specific_module=general_query and specific_module,
                rh_scope=general_query and rh_scope,
            )
            scored.append((score, item, facts, specific_module, rh_scope))
        return sorted(scored, key=lambda item: (-item[0], -float(item[1].quality_score or 0.0), item[1].evidence_id))

    def _scope_text(self, evidence) -> str:
        return " ".join(
            filter(None, [evidence.module_model, evidence.device_family, evidence.manual_title, evidence.section, evidence.text[:160]])
        )

    def _is_rh_scope(self, evidence) -> bool:
        return bool(re.search(r"S7-1500R/H|S7-1500\s+R/H|\bR/H\b", self._scope_text(evidence), re.I))

    def _is_specific_module(self, evidence) -> bool:
        return bool(
            re.search(
                r"\bCPU\s*15\d{2}|\b(?:PS|PM|SM|TM|IM|CM|CP)\s+[A-Z0-9]|\b6ES7[A-Z0-9-]+",
                self._scope_text(evidence),
                re.I,
            )
        )

    def _is_system_level(self, evidence) -> bool:
        value = self._scope_text(evidence)
        return bool(
            re.search(r"system manual|系统手册|操作规则和规定|系统级接线|S7-1500\s*/\s*ET\s*200MP", value, re.I)
        ) and not self._is_rh_scope(evidence)

    def _is_general_query(self, query: str) -> bool:
        return not bool(
            re.search(r"\bCPU\s*15\d{2}|\b(?:PS|PM|SM|TM|IM|CM|CP)\s+[A-Z0-9]|\b6ES7[A-Z0-9-]+", query, re.I)
        )
