#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from ..config import SafePLCConfig
from ..schemas import AgentEvidence


EXCLUDED_BUNDLE_PARTS = (
    "trusted_rag",
    "multimodal_guard",
    "secguard",
    "redteam_cases",
    "mepi_visual_guard_cases",
    "poison",
)


DOMAIN_TERMS = [
    "PROFINET",
    "PROFIBUS",
    "HMI",
    "CPU",
    "ET 200MP",
    "S7-1500",
    "X1",
    "X2",
    "EMC",
    "电源电压",
    "输入电压",
    "电流",
    "功率",
    "端子",
    "接线",
    "拓扑",
    "环网",
    "指示灯",
    "报警",
    "通信",
    "屏蔽",
    "接地",
]


def is_excluded_path(path: str) -> bool:
    low = str(path).replace("\\", "/").lower()
    return any(part in low for part in EXCLUDED_BUNDLE_PARTS)


class ToolRegistry:
    """Unified retrieval facade used by all agents."""

    def __init__(self, config: SafePLCConfig):
        self.config = config
        self._evidence = self._load_evidence()
        self.tool_call_count = 0
        self.last_latency_ms = 0

    def search_text(
        self,
        query: str,
        filters: Optional[Dict[str, str]] = None,
        top_k: int = 3,
    ) -> List[AgentEvidence]:
        return self._search(query, modalities={"text", "table", "policy"}, filters=filters, top_k=top_k, tool="search_text")

    def search_table(
        self,
        query: str,
        filters: Optional[Dict[str, str]] = None,
        top_k: int = 3,
    ) -> List[AgentEvidence]:
        return self._search(query, modalities={"table"}, filters=filters, top_k=top_k, tool="search_table")

    def search_figure(
        self,
        query: str,
        filters: Optional[Dict[str, str]] = None,
        top_k: int = 3,
    ) -> List[AgentEvidence]:
        return self._search(query, modalities={"figure", "visual"}, filters=filters, top_k=top_k, tool="search_figure")

    def search_hybrid(
        self,
        query: str,
        modalities: Optional[List[str]] = None,
        filters: Optional[Dict[str, str]] = None,
        top_k: int = 4,
    ) -> List[AgentEvidence]:
        allowed = set(modalities or ["text", "table", "figure", "visual", "policy"])
        return self._search(query, modalities=allowed, filters=filters, top_k=top_k, tool="search_hybrid")

    def fetch_page(self, page_id: str) -> Optional[AgentEvidence]:
        self.tool_call_count += 1
        for ev in self._evidence:
            if str(ev.page or "") == str(page_id):
                return ev
        return None

    def fetch_figure(self, figure_id: str) -> Optional[AgentEvidence]:
        self.tool_call_count += 1
        for ev in self._evidence:
            if ev.figure_id == figure_id:
                return ev
        return None

    def _search(
        self,
        query: str,
        modalities: Iterable[str],
        filters: Optional[Dict[str, str]],
        top_k: int,
        tool: str,
    ) -> List[AgentEvidence]:
        started = time.perf_counter()
        self.tool_call_count += 1
        allowed = {m.lower() for m in modalities}
        filters = filters or {}

        scored: List[AgentEvidence] = []
        for ev in self._evidence:
            if ev.modality.lower() not in allowed:
                continue
            if not self._matches_filters(ev, filters):
                continue
            score = self._score(query, ev)
            if score <= 0:
                continue
            clone = self._clone(ev)
            clone.retrieval_score = score
            clone.metadata = dict(clone.metadata or {})
            clone.metadata["retrieval_tool"] = tool
            scored.append(clone)

        scored.sort(key=lambda x: x.retrieval_score, reverse=True)
        self.last_latency_ms = int((time.perf_counter() - started) * 1000)
        return scored[: max(1, top_k)]

    def _matches_filters(self, ev: AgentEvidence, filters: Dict[str, str]) -> bool:
        for key, value in filters.items():
            if not value:
                continue
            actual = str(getattr(ev, key, "") or ev.metadata.get(key, "")).lower()
            if str(value).lower() not in actual:
                return False
        return True

    def _score(self, query: str, ev: AgentEvidence) -> float:
        haystack = " ".join(
            [
                ev.source,
                ev.modality,
                ev.title,
                ev.module,
                ev.order_number,
                ev.parameter,
                ev.section,
                ev.figure_id,
                ev.text,
            ]
        ).lower()
        tokens = self._tokens(query)
        if not tokens:
            return 0.0

        score = 0.0
        for token in tokens:
            t = token.lower()
            if t in haystack:
                score += 1.0
                if t in ev.title.lower() or t in ev.parameter.lower() or t in ev.module.lower():
                    score += 0.6
        if score <= 0:
            return 0.0
        if ev.page is not None:
            score += 0.2
        if ev.figure_id:
            score += 0.2
        return round(score, 4)

    def _tokens(self, query: str) -> List[str]:
        text = query or ""
        tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_/\-]*|[\u4e00-\u9fff]{2,}", text)
        for term in DOMAIN_TERMS:
            if term.lower() in text.lower() and term not in tokens:
                tokens.append(term)
        return list(dict.fromkeys(tokens))

    def _load_evidence(self) -> List[AgentEvidence]:
        if self.config.mode == "FULL" and self.config.full_assets_available():
            full = self._load_full_jsonl()
            if full:
                return full
        return self._sample_evidence()

    def _load_full_jsonl(self) -> List[AgentEvidence]:
        records: List[AgentEvidence] = []
        for raw_path in [self.config.chunks_jsonl, self.config.pages_jsonl]:
            if not raw_path or is_excluded_path(raw_path):
                continue
            path = Path(raw_path)
            if not path.exists():
                continue
            with path.open("r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    source = str(data.get("source", data.get("doc", path.name)))
                    if is_excluded_path(source):
                        continue
                    text = str(data.get("text", data.get("content", data.get("chunk", ""))) or "")
                    if not text.strip():
                        continue
                    modality = str(data.get("modality", data.get("type", "text")) or "text")
                    records.append(
                        self._make_evidence(
                            source=source,
                            source_type="full_jsonl",
                            modality=modality,
                            text=text,
                            page=data.get("page", data.get("page_no")),
                            section=str(data.get("section", "")),
                            figure_id=str(data.get("figure_id", data.get("fig_id", "")) or ""),
                            title=str(data.get("title", data.get("heading", "")) or ""),
                            module=str(data.get("module", data.get("model", "")) or ""),
                            order_number=str(data.get("order_number", "")),
                            parameter=str(data.get("parameter", data.get("param", "")) or ""),
                            metadata={"raw_path": str(path)},
                        )
                    )
        return records

    def _sample_evidence(self) -> List[AgentEvidence]:
        return [
            self._make_evidence(
                source="SAMPLE S7-1500 / ET 200MP manual extract",
                source_type="sample_manual",
                modality="table",
                page=6313,
                title="PS 60W 24/48/60VDC HF power supply input range",
                module="PS 60W 24/48/60VDC HF",
                order_number="6ES7505-0RB00-0AB0",
                parameter="电源电压允许范围",
                text=(
                    "PS 60W 24/48/60VDC HF 的额定输入为 24 V DC、48 V DC、60 V DC；"
                    "允许范围下限为静态 19.2 V、动态 18.5 V；上限为静态 72 V、动态 75.5 V。"
                ),
            ),
            self._make_evidence(
                source="SAMPLE S7-1500 / ET 200MP manual extract",
                source_type="sample_manual",
                modality="figure",
                page=2478,
                figure_id="fig_cpu1517_3pn_x1_x2",
                title="CPU 1517-3 PN front interface layout",
                module="CPU 1517-3 PN",
                parameter="PROFINET interface X1 X2",
                text=(
                    "CPU 1517-3 PN 前面板图显示 PROFINET 接口 X1 和 X2；"
                    "X1 常用于 IO/现场网络连接，X2 可用于上位网络或工程网络，具体以项目组态为准。"
                ),
            ),
            self._make_evidence(
                source="SAMPLE PROFINET topology note",
                source_type="sample_manual",
                modality="figure",
                page=3901,
                figure_id="fig_profinet_hmi_cpu_topology",
                title="PROFINET topology with HMI and CPU",
                module="S7-1500 CPU / HMI",
                parameter="PROFINET topology",
                text=(
                    "HMI 与 CPU 通过 PROFINET 通信时应连接到 CPU 的 PROFINET 接口；"
                    "拓扑图保留设备名称、IP/设备名和交换机/环网关系，接线应与组态一致。"
                ),
            ),
            self._make_evidence(
                source="SAMPLE wiring and terminal note",
                source_type="sample_manual",
                modality="text",
                page=1202,
                title="Wiring and terminal safety note",
                module="S7-1500 / ET 200MP",
                parameter="端子接线注意事项",
                text=(
                    "接线、拆线和端子检查应在停机、断电、确认无电压并由具备资质人员执行；"
                    "线缆编号、端子定义和屏蔽层连接应与图纸和设备手册一致。"
                ),
            ),
            self._make_evidence(
                source="SAMPLE EMC installation note",
                source_type="sample_manual",
                modality="text",
                page=560,
                title="EMC grounding and shielding",
                module="S7-1500 / ET 200MP",
                parameter="EMC 接地 屏蔽 线缆布置",
                text=(
                    "EMC 相关安装应关注低阻抗接地、屏蔽层正确连接、动力线与信号线分开布置，"
                    "并避免强干扰线缆与通信线缆长距离平行敷设。"
                ),
            ),
            self._make_evidence(
                source="SAMPLE troubleshooting note",
                source_type="sample_manual",
                modality="text",
                page=3120,
                title="Communication fault and LED troubleshooting",
                module="CPU / PROFINET device",
                parameter="通信异常 指示灯 报警",
                text=(
                    "通信不上且 CPU 或设备指示灯异常时，先记录 LED 状态、报警诊断、设备名/IP、"
                    "PROFINET 连接状态、供电状态和最近组态变更；无法由资料确认的现场状态需要人工复核。"
                ),
            ),
            self._make_evidence(
                source="SafePLC offline industrial operation boundary",
                source_type="system_boundary",
                modality="policy",
                page=None,
                title="OFFLINE READ-ONLY operation boundary",
                module="SafePLC-Assist Box",
                parameter="工业操作安全边界",
                text=(
                    "系统仅提供离线资料查证、教学实训辅助和运维记录整理；"
                    "不得连接或控制真实 PLC，不输出短接、绕过、屏蔽安全功能、带电接线或强制输出的操作步骤。"
                ),
            ),
        ]

    def _make_evidence(self, **kwargs: object) -> AgentEvidence:
        page = kwargs.get("page")
        try:
            page_value = int(page) if page not in {None, ""} else None
        except (TypeError, ValueError):
            page_value = None
        temp = AgentEvidence(
            evidence_id="",
            source=str(kwargs.get("source", "")),
            source_type=str(kwargs.get("source_type", "")),
            modality=str(kwargs.get("modality", "text")),
            page=page_value,
            section=str(kwargs.get("section", "")),
            figure_id=str(kwargs.get("figure_id", "")),
            title=str(kwargs.get("title", "")),
            module=str(kwargs.get("module", "")),
            order_number=str(kwargs.get("order_number", "")),
            parameter=str(kwargs.get("parameter", "")),
            text=str(kwargs.get("text", "")),
            retrieval_score=float(kwargs.get("retrieval_score", 0.0) or 0.0),
            metadata=dict(kwargs.get("metadata", {}) or {}),
        )
        digest = hashlib.sha256(temp.signature().encode("utf-8")).hexdigest()[:12]
        temp.evidence_id = f"ev_{digest}"
        return temp

    def _clone(self, ev: AgentEvidence) -> AgentEvidence:
        return AgentEvidence(
            evidence_id=ev.evidence_id,
            source=ev.source,
            source_type=ev.source_type,
            modality=ev.modality,
            page=ev.page,
            section=ev.section,
            figure_id=ev.figure_id,
            title=ev.title,
            module=ev.module,
            order_number=ev.order_number,
            parameter=ev.parameter,
            text=ev.text,
            retrieval_score=ev.retrieval_score,
            agent_names=list(ev.agent_names),
            claim_links=list(ev.claim_links),
            conflict_with=list(ev.conflict_with),
            metadata=dict(ev.metadata or {}),
        )
