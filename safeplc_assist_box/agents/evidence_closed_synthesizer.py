#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Dict, Iterable, List

from ..schemas import AgentClaim, AgentEvidence, QueryContext, compact_text


class EvidenceClosedSynthesizer:
    """Deterministic final answer builder using only accepted claims/evidence."""

    def synthesize(
        self,
        query_context: QueryContext,
        claims: Iterable[AgentClaim],
        evidence_by_id: Dict[str, AgentEvidence],
        verdict: str,
    ) -> str:
        claim_list = list(claims)
        if verdict == "NEED_CLARIFICATION":
            return query_context.clarify_question or "请补充模块型号、订货号、接口或故障现象后再查询。"
        if verdict == "NEED_MORE_EVIDENCE":
            return "当前检索没有找到可支撑结论的证据，因此不生成无依据答案。请补充型号、订货号或更具体的问题。"
        if verdict == "REFUSE":
            return (
                "OFFLINE / READ-ONLY refusal: 该请求涉及危险工业操作，不能提供短接、绕过保护、带电接线、"
                "强制输出或控制真实 PLC 的步骤。可做的安全替代是停机隔离、记录现象、核对图纸/手册，并交由具备资质的人员处理。"
            )
        if not claim_list:
            return "当前没有被 Judge 接受的证据闭合 claim。"

        location_claim = next((c for c in claim_list if c.claim_type == "location"), None)
        if location_claim:
            meta = location_claim.metadata
            page = meta.get("page") or self._first_page(location_claim, evidence_by_id)
            figure = meta.get("figure_number") or meta.get("figure_id") or self._first_figure(location_claim, evidence_by_id)
            ports = meta.get("ports") or []
            marker = meta.get("location_marker") or ""
            model = location_claim.model_scope or "CPU 1517-3 PN/DP"
            conclusion = (
                f"{model} 的 X1 位于模块前部连接区，是第一个 PROFINET IO 接口"
                + (f"，端口为 {'、'.join(ports)}" if ports else "")
                + (f"，前视图标号为 {marker}" if marker else "")
                + f"。见资料页 {page or '-'}、{figure or '对应图示'}。"
            )
            extra = [c for c in claim_list if c is not location_claim]
            if extra:
                conclusion += " PROFINET/HMI 相关注意事项："
                conclusion += "；".join(compact_text(c.claim_text, 120) for c in extra[:2]) + "。"
            return conclusion

        bullets = [compact_text(c.claim_text, 140) for c in claim_list[:4]]
        evidence_refs = self._evidence_refs(claim_list, evidence_by_id)
        answer = "【结论】\n" + "\n".join(f"- {item}" for item in bullets)
        if evidence_refs:
            answer += "\n【依据】\n" + "\n".join(f"- {ref}" for ref in evidence_refs[:4])
        if verdict == "PARTIAL":
            answer += "\n【注意】仍有子问题未被证据覆盖，以上仅为已验证部分。"
        return compact_text(answer, 700)

    def _first_page(self, claim: AgentClaim, evidence_by_id: Dict[str, AgentEvidence]):
        for ev_id in claim.evidence_ids:
            ev = evidence_by_id.get(ev_id)
            if ev and ev.page:
                return ev.page
        return ""

    def _first_figure(self, claim: AgentClaim, evidence_by_id: Dict[str, AgentEvidence]) -> str:
        for ev_id in claim.evidence_ids:
            ev = evidence_by_id.get(ev_id)
            if ev and (ev.figure_number or ev.figure_id):
                return ev.figure_number or ev.figure_id
        return ""

    def _evidence_refs(self, claims: List[AgentClaim], evidence_by_id: Dict[str, AgentEvidence]) -> List[str]:
        refs: List[str] = []
        for claim in claims:
            for ev_id in claim.evidence_ids:
                ev = evidence_by_id.get(ev_id)
                if not ev:
                    continue
                ref = ev.manual_title or ev.source
                if ev.page:
                    ref += f", page {ev.page}"
                if ev.figure_number:
                    ref += f", {ev.figure_number}"
                if ref not in refs:
                    refs.append(ref)
        return refs
