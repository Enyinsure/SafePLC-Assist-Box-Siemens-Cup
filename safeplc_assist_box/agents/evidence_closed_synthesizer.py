#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Dict, Iterable, List

from ..schemas import AgentClaim, AgentEvidence, QueryContext, compact_text


class EvidenceClosedSynthesizer:
    """Deterministic answer builder restricted to Judge-accepted claims and evidence."""

    def synthesize(
        self,
        query_context: QueryContext,
        claims: Iterable[AgentClaim],
        evidence_by_id: Dict[str, AgentEvidence],
        verdict: str,
    ) -> str:
        accepted = list(claims)
        if verdict == "NEED_CLARIFICATION":
            return query_context.clarify_question or "请补充模块型号、订货号、接口名称或关键现场条件后再查证。"
        if verdict == "NEED_MORE_EVIDENCE":
            return "检索后仍缺少可直接支撑结论的证据；系统不补写经验常识。可在确认 collection、embedding 和型号后进行一次受控复检索。"
        if verdict == "ABSTAIN":
            return "已完成当前范围内的检索，但没有可靠证据可以确认该结论，因此本次不作答。请核对型号、订货号或资料范围。"
        if verdict == "REFUSE":
            return (
                "OFFLINE / READ-ONLY：该请求涉及危险工业操作，不能提供短接、旁路保护、带电接线、强制输出或控制真实 PLC 的步骤。"
                "请停机隔离、记录现象、核对图纸和手册，并交由具备资质人员处理。"
            )
        if not accepted:
            return "当前没有通过 Judge 的证据闭合结论。"

        answer_parts: List[str] = []
        location = next((claim for claim in accepted if claim.claim_type == "location"), None)
        if location:
            answer_parts.append(self._location_text(location, evidence_by_id))
        for claim in accepted:
            if claim is location:
                continue
            text = compact_text(claim.claim_text, 110)
            if claim.metadata.get("general_guidance"):
                text = "通用 PROFINET 指南：" + text.removeprefix("General PROFINET guidance:").strip()
            answer_parts.append(text)

        references = self._evidence_refs(accepted, evidence_by_id)
        answer = "【结论】" + "；".join(part.rstrip("。") for part in answer_parts[:4]) + "。"
        if references:
            answer += "【依据】" + "；".join(references[:3]) + "。"
        used_evidence = [
            evidence_by_id[item]
            for claim in accepted
            for item in claim.evidence_ids
            if item in evidence_by_id
        ]
        if any(item.visual_evidence_status == "page_text_only" for item in used_evidence):
            answer += "【限制】目前仅有图示页文字证据，未确认可显示的图片文件。"
        if verdict == "PARTIAL":
            answer += "【待确认】仍有子问题未被可靠证据覆盖，以上只包含已查证部分。"
        return compact_text(answer, 520)

    def _location_text(self, claim: AgentClaim, evidence_by_id: Dict[str, AgentEvidence]) -> str:
        metadata = claim.metadata
        evidence = next((evidence_by_id[item] for item in claim.evidence_ids if item in evidence_by_id), None)
        model = claim.model_scope or (evidence.module_model if evidence else "目标模块")
        page = metadata.get("page") or (evidence.page if evidence else "")
        figure = metadata.get("figure_number") or metadata.get("figure_id") or (
            evidence.figure_number or evidence.figure_id if evidence else ""
        )
        marker = metadata.get("location_marker") or ""
        ports = list(metadata.get("ports") or [])
        text = f"{model} 的 X1 位于模块前部连接区域"
        if ports:
            text += f"，端口为 {'、'.join(ports)}"
        if marker:
            text += f"，前视图标号为 {marker}"
        if page or figure:
            text += f"，见资料页 {page or '-'}、{figure or '对应图示'}"
        return text

    def _evidence_refs(self, claims: List[AgentClaim], evidence_by_id: Dict[str, AgentEvidence]) -> List[str]:
        references: List[str] = []
        for claim in claims:
            for evidence_id in claim.evidence_ids:
                evidence = evidence_by_id.get(evidence_id)
                if not evidence:
                    continue
                parts = [evidence.manual_title or evidence.source]
                if evidence.module_model:
                    parts.append(evidence.module_model)
                if evidence.order_number:
                    parts.append(evidence.order_number)
                if evidence.page is not None:
                    parts.append(f"页 {evidence.page}")
                if evidence.figure_number:
                    parts.append(evidence.figure_number)
                reference = "，".join(filter(None, parts))
                if reference not in references:
                    references.append(reference)
        return references
