#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Dict, List

from ..schemas import (
    AgentResult,
    AgentStatus,
    EvidencePool,
    JudgeConfidence,
    JudgeDecision,
    JudgeVerdict,
    QueryContext,
)


class JudgeAgent:
    role_description = "Evidence-closed decision agent for accepting, rejecting and conflict-checking specialist results."

    def decide(
        self,
        query_context: QueryContext,
        results: List[AgentResult],
        evidence_pool: EvidencePool,
    ) -> JudgeDecision:
        accepted: List[str] = []
        rejected: List[str] = []
        supported: List[str] = []
        unsupported: List[str] = []
        final_ids: List[str] = []

        for result in results:
            has_evidence = bool(result.evidence_ids)
            if result.status in {AgentStatus.ANSWERED.value, AgentStatus.PARTIAL.value, AgentStatus.REFUSE.value} and has_evidence:
                accepted.append(result.agent_name)
                supported.append(result.answer_fragment)
                final_ids.extend(result.evidence_ids)
            else:
                rejected.append(result.agent_name)
                reason = result.abstain_reason or "Result has no cited evidence."
                unsupported.append(f"{result.agent_name}: {reason}")

        final_ids = list(dict.fromkeys(final_ids))
        conflict_groups = list(evidence_pool.conflicts)
        for result in results:
            for conflict in result.conflicts:
                conflict_groups.append({"agents": [result.agent_name], "reason": conflict, "evidence_ids": result.evidence_ids})
        conflicting_claims = [
            str(group.get("reason", group)) for group in conflict_groups if isinstance(group, dict)
        ]

        need_clarification = bool(query_context.missing_slots) or any(
            r.status == AgentStatus.NEED_CLARIFICATION.value for r in results
        )
        need_more_evidence = not final_ids and not need_clarification

        if need_clarification:
            verdict = JudgeVerdict.NEED_CLARIFICATION.value
            confidence = JudgeConfidence.NOT_AVAILABLE.value
            decision_reason = "关键槽位缺失，无法可靠裁决。"
            final_answer = query_context.clarify_question or "请补充关键设备信息后重新查询。"
        elif not accepted:
            verdict = JudgeVerdict.REVIEW.value
            confidence = JudgeConfidence.NOT_AVAILABLE.value
            decision_reason = "没有 Agent 输出被证据池支持。"
            final_answer = "当前证据不足，系统不生成无依据结论；请补充型号、订货号、接口或故障现象。"
        elif conflict_groups:
            verdict = JudgeVerdict.CONFLICT.value
            confidence = JudgeConfidence.CONFLICT.value
            decision_reason = "Agent 输出或证据存在冲突，不能按多数答案直接裁决。"
            final_answer = self._compose_answer(supported, final_ids, conflict=True)
        elif unsupported:
            verdict = JudgeVerdict.REVIEW.value
            confidence = JudgeConfidence.MEDIUM.value
            decision_reason = "部分 Agent 输出无证据或已 abstain，最终答案仅采纳有证据片段。"
            final_answer = self._compose_answer(supported, final_ids)
        else:
            verdict = JudgeVerdict.PASS.value
            confidence = JudgeConfidence.HIGH.value if len(final_ids) >= 1 else JudgeConfidence.LOW.value
            decision_reason = "已采纳的 Agent 输出均引用了 Evidence Pool 证据。"
            final_answer = self._compose_answer(supported, final_ids)

        return JudgeDecision(
            accepted_agent_outputs=accepted,
            rejected_agent_outputs=rejected,
            conflict_groups=conflict_groups,
            supported_claims=supported,
            unsupported_claims=unsupported,
            conflicting_claims=conflicting_claims,
            final_evidence_ids=final_ids,
            need_more_evidence=need_more_evidence,
            need_clarification=need_clarification,
            final_answer=final_answer,
            verdict=verdict,
            confidence=confidence,
            decision_reason=decision_reason,
            metadata={"judge_role": self.role_description},
        )

    def _compose_answer(self, supported: List[str], evidence_ids: List[str], conflict: bool = False) -> str:
        if not supported:
            return "没有可采纳的证据支撑结论。"
        prefix = "【裁决】存在冲突，以下仅为已证据支撑的片段，需人工复核。\n" if conflict else "【裁决】基于证据池采纳以下结论。\n"
        body = "\n".join(f"- {item}" for item in supported if item)
        evidence = "、".join(evidence_ids)
        return f"{prefix}{body}\n【最终证据】{evidence}\n【边界】仅用于离线资料查证和教学实训，不控制真实 PLC。"
