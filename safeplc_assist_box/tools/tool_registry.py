#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

from ..config import SafePLCConfig
from ..evidence.evidence_ranker import rank_evidence
from ..evidence.model_identity import reject_cross_family
from ..schemas import AgentEvidence
from .chroma_figure_retriever import ChromaFigureRetriever
from .chroma_text_retriever import ChromaTextRetriever, ChromaUnavailable
from .embedding_adapter import EmbeddingAdapter
from .jsonl_fallback_retriever import JSONLFallbackRetriever
from .metadata_normalizer import normalize_metadata


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
    "voltage",
    "current",
    "power",
    "terminal",
    "wiring",
    "topology",
    "shielding",
    "grounding",
]


class ToolRegistry:
    """Unified retrieval facade used by all agents.

    SAMPLE mode is a small deterministic fixture. FULL mode never silently
    returns SAMPLE evidence: Chroma is attempted first and JSONL is used only
    when SAFEPLC_ALLOW_JSONL_FALLBACK=1.
    """

    def __init__(self, config: SafePLCConfig, feature_switches: Optional[Dict[str, bool]] = None):
        self.config = config
        self.feature_switches = feature_switches or {}
        self.tool_call_count = 0
        self.last_latency_ms = 0
        self.errors: List[str] = []
        self.backend_audit: Dict[str, object] = {
            "mode": config.mode,
            "text_backend_active": False,
            "figure_backend_active": False,
            "jsonl_fallback_active": False,
            "sample_fixture_active": config.mode != "FULL",
            "errors": self.errors,
        }
        self._sample_evidence = self._build_sample_evidence() if config.mode != "FULL" else []
        self._text_retriever: Optional[ChromaTextRetriever] = None
        self._figure_retriever: Optional[ChromaFigureRetriever] = None
        self._jsonl_chunks: Optional[JSONLFallbackRetriever] = None
        self._jsonl_pages: Optional[JSONLFallbackRetriever] = None
        self._figure_jsonl: Optional[JSONLFallbackRetriever] = None
        self._init_full_backends()

    def search_text(
        self,
        query: str,
        filters: Optional[Dict[str, str]] = None,
        top_k: int = 4,
    ) -> List[AgentEvidence]:
        return self._search(query, {"text", "table", "policy"}, filters=filters, top_k=top_k, tool="search_text")

    def search_table(
        self,
        query: str,
        filters: Optional[Dict[str, str]] = None,
        top_k: int = 4,
    ) -> List[AgentEvidence]:
        return self._search(query, {"table"}, filters=filters, top_k=top_k, tool="search_table")

    def search_figure(
        self,
        query: str,
        filters: Optional[Dict[str, str]] = None,
        top_k: int = 4,
    ) -> List[AgentEvidence]:
        return self._search(query, {"figure", "visual"}, filters=filters, top_k=top_k, tool="search_figure")

    def search_hybrid(
        self,
        query: str,
        modalities: Optional[List[str]] = None,
        filters: Optional[Dict[str, str]] = None,
        top_k: int = 6,
    ) -> List[AgentEvidence]:
        allowed = set(modalities or ["text", "table", "figure", "visual", "policy"])
        return self._search(query, allowed, filters=filters, top_k=top_k, tool="search_hybrid")

    def fetch_page(self, page_id: str) -> Optional[AgentEvidence]:
        self.tool_call_count += 1
        for ev in self._sample_evidence:
            if str(ev.page or "") == str(page_id):
                return ev
        return None

    def fetch_figure(self, figure_id: str) -> Optional[AgentEvidence]:
        self.tool_call_count += 1
        for ev in self._sample_evidence:
            if ev.figure_id == figure_id or ev.figure_number == figure_id:
                return ev
        return None

    def _init_full_backends(self) -> None:
        if self.config.mode != "FULL":
            return
        embedding_adapter = EmbeddingAdapter.from_config(self.config)
        if self.config.chroma_dir and Path(self.config.chroma_dir).exists():
            self._text_retriever = ChromaTextRetriever(
                self.config.chroma_dir,
                self.config.text_collection,
                embedding_adapter=embedding_adapter,
            )
            self.backend_audit["text_backend_active"] = True
        elif not self.config.allow_jsonl_fallback:
            self.errors.append("FULL text Chroma unavailable and SAFEPLC_ALLOW_JSONL_FALLBACK is not enabled.")

        if (
            self.feature_switches.get("enable_figure_backend", True)
            and self.config.figure_chroma_dir
            and Path(self.config.figure_chroma_dir).exists()
        ):
            self._figure_retriever = ChromaFigureRetriever(
                self.config.figure_chroma_dir,
                self.config.figure_collection,
                self.config.figure_cards_jsonl,
                self.config.visual_dir,
                embedding_adapter=embedding_adapter,
            )
            self.backend_audit["figure_backend_active"] = True
        elif self.config.require_figure_backend:
            self.errors.append("FULL figure Chroma is required but SAFEPLC_FIGURE_CHROMA_DIR is missing.")

        if self.config.allow_jsonl_fallback:
            self._jsonl_chunks = JSONLFallbackRetriever([self.config.chunks_jsonl], "jsonl_chunks", "text")
            self._jsonl_pages = JSONLFallbackRetriever([self.config.pages_jsonl], "jsonl_pages", "text")
            self._figure_jsonl = JSONLFallbackRetriever(
                [self.config.figure_chunks_jsonl, self.config.figure_cards_jsonl],
                "jsonl_chunks",
                "figure",
            )
            if any(r and r.available() for r in [self._jsonl_chunks, self._jsonl_pages, self._figure_jsonl]):
                self.backend_audit["jsonl_fallback_active"] = True

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
        if not self.feature_switches.get("enable_figure_backend", True):
            allowed -= {"figure", "visual"}
        if self.config.mode == "FULL":
            records = self._search_full(query, allowed, top_k=max(top_k, 8))
        else:
            records = self._search_sample(query, allowed, filters=filters, top_k=max(top_k, 8), tool=tool)
        if self.feature_switches.get("enable_model_filter", True):
            records = reject_cross_family(records, query)
        if self.feature_switches.get("enable_evidence_reranker", True):
            records = rank_evidence(
                records,
                query=query,
                required_modality="figure" if allowed & {"figure", "visual"} and not allowed & {"text", "table"} else None,
                top_k=top_k,
            )
        self.last_latency_ms = int((time.perf_counter() - started) * 1000)
        return records[: max(1, top_k)]

    def _search_full(self, query: str, allowed: Set[str], top_k: int) -> List[AgentEvidence]:
        out: List[AgentEvidence] = []
        need_text = bool(allowed & {"text", "table", "policy"})
        need_figure = bool(allowed & {"figure", "visual"})

        if need_figure and self._figure_retriever:
            try:
                out.extend(self._figure_retriever.search(query, top_k=top_k))
            except ChromaUnavailable as exc:
                self.errors.append(str(exc))

        if need_text and self._text_retriever:
            try:
                out.extend(self._text_retriever.search(query, top_k=top_k))
            except ChromaUnavailable as exc:
                self.errors.append(str(exc))

        if self.config.allow_jsonl_fallback:
            if need_figure and self._figure_jsonl and self._figure_jsonl.available():
                out.extend(self._figure_jsonl.search(query, top_k=top_k, modalities=allowed))
            if need_text and self._jsonl_chunks and self._jsonl_chunks.available():
                out.extend(self._jsonl_chunks.search(query, top_k=top_k, modalities=allowed))
            if need_text and self._jsonl_pages and self._jsonl_pages.available():
                out.extend(self._jsonl_pages.search(query, top_k=top_k, modalities=allowed))

        if not out and not self.config.allow_jsonl_fallback and not (self._text_retriever or self._figure_retriever):
            self.errors.append("FULL retrieval returned no evidence because no active backend is available.")
        return out

    def _search_sample(
        self,
        query: str,
        allowed: Set[str],
        filters: Optional[Dict[str, str]],
        top_k: int,
        tool: str,
    ) -> List[AgentEvidence]:
        filters = filters or {}
        scored: List[AgentEvidence] = []
        for ev in self._sample_evidence:
            if ev.modality.lower() not in allowed:
                continue
            if not self._matches_filters(ev, filters):
                continue
            score = self._score(query, ev)
            if score <= 0:
                continue
            clone = self._clone(ev)
            clone.retrieval_score = score
            clone.normalized_score = score
            clone.metadata["retrieval_tool"] = tool
            scored.append(clone)
        scored.sort(key=lambda x: x.retrieval_score, reverse=True)
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
                ev.manual_title,
                ev.module_model,
                ev.order_number,
                ev.parameter,
                ev.section,
                ev.figure_id,
                ev.figure_number,
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
                if t in ev.manual_title.lower() or t in ev.parameter.lower() or t in ev.module_model.lower():
                    score += 0.6
        if score <= 0:
            return 0.0
        if ev.page is not None:
            score += 0.2
        if ev.figure_id or ev.figure_number:
            score += 0.35
        if ev.direct_evidence:
            score += 0.4
        return round(min(score / max(len(tokens), 1), 1.0), 6)

    def _tokens(self, query: str) -> List[str]:
        text = query or ""
        tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_/\-]*|[\u4e00-\u9fff]{2,}", text)
        for term in DOMAIN_TERMS:
            if term.lower() in text.lower() and term not in tokens:
                tokens.append(term)
        return list(dict.fromkeys(tokens))

    def _sample(self, **kwargs: object) -> AgentEvidence:
        ev = normalize_metadata(
            text=str(kwargs.pop("text")),
            metadata=dict(kwargs),
            backend=str(kwargs.get("retrieval_backend") or "sample_fixture"),
            query_text="",
            collection_name="sample_fixture",
            fallback_score=float(kwargs.get("retrieval_score", 0.8) or 0.8),
            modality_hint=str(kwargs.get("modality", "text")),
        )
        ev.direct_evidence = bool(kwargs.get("direct_evidence", False))
        ev.quality_score = ev.retrieval_score
        ev.metadata["direct_evidence"] = ev.direct_evidence
        return ev

    def _build_sample_evidence(self) -> List[AgentEvidence]:
        return [
            self._sample(
                source="SAMPLE S7-1500 CPU manual extract",
                source_type="sample_manual",
                modality="figure",
                page=2476,
                figure_id="fig_cpu1517_3pn_x1_x2",
                figure_number="Figure 2-237",
                title="CPU 1517-3 PN/DP front view",
                manual_title="S7-1500 CPU manual",
                module_model="CPU 1517-3 PN/DP",
                order_number="6ES7517-3AP00-0AB0",
                parameter="X1 PROFINET interface",
                direct_evidence=True,
                text=(
                    "CPU 1517-3 PN/DP front view. Figure 2-237 marks X1 as the first PROFINET IO "
                    "interface in the lower front connector area. Marker ⑦ points to X1. "
                    "The interface has two RJ45 ports: X1 P1 and X1 P2."
                ),
            ),
            self._sample(
                source="SAMPLE S7-1500 CPU technical data",
                source_type="sample_manual",
                modality="table",
                page=2477,
                title="CPU 1517-3 PN/DP interface data",
                manual_title="S7-1500 CPU manual",
                module_model="CPU 1517-3 PN/DP",
                order_number="6ES7517-3AP00-0AB0",
                parameter="X1 port count",
                direct_evidence=True,
                text="CPU 1517-3 PN/DP X1 is a PROFINET IO interface with ports X1 P1 and X1 P2.",
            ),
            self._sample(
                source="SAMPLE PROFINET general guide",
                source_type="sample_manual",
                modality="text",
                page=3901,
                title="PROFINET with HMI and CPU",
                manual_title="General PROFINET guide",
                device_family="S7-1500",
                module_model="S7-1500 general",
                parameter="PROFINET topology",
                direct_evidence=False,
                text=(
                    "General PROFINET guidance: HMI and CPU communication requires consistent device "
                    "names, unique IP addresses in the project network, matching topology, and verified "
                    "physical cabling to the intended PROFINET interface."
                ),
            ),
            self._sample(
                source="SAMPLE S7-1500 / ET 200MP manual extract",
                source_type="sample_manual",
                modality="table",
                page=6313,
                title="PS 60W 24/48/60VDC HF power supply input range",
                manual_title="S7-1500 / ET 200MP manual",
                module_model="PS 60W 24/48/60VDC HF",
                order_number="6ES7505-0RB00-0AB0",
                parameter="input voltage range",
                direct_evidence=True,
                text=(
                    "PS 60W 24/48/60VDC HF rated inputs are 24 V DC, 48 V DC and 60 V DC. "
                    "The permitted static range is 19.2 V to 72 V; the dynamic range is 18.5 V to 75.5 V."
                ),
            ),
            self._sample(
                source="SAMPLE wiring and terminal note",
                source_type="sample_manual",
                modality="text",
                page=1202,
                title="Wiring and terminal safety note",
                manual_title="S7-1500 / ET 200MP manual",
                module_model="S7-1500 / ET 200MP",
                parameter="terminal wiring",
                text=(
                    "Wiring, removing wires and terminal checks should be performed after stop, isolation, "
                    "power-off verification and qualified review by 具备资质 personnel. 端子接线注意事项包括核对线缆编号、"
                    "terminal definitions and shield connections against drawings and manuals."
                ),
            ),
            self._sample(
                source="SAMPLE EMC installation note",
                source_type="sample_manual",
                modality="text",
                page=560,
                title="EMC grounding and shielding",
                manual_title="S7-1500 / ET 200MP manual",
                module_model="S7-1500 / ET 200MP",
                parameter="EMC grounding shielding cable layout",
                text=(
                    "EMC installation should use low-impedance grounding, correct shield termination, "
                    "separation of power and signal cables, and avoid long parallel runs near strong interference."
                ),
            ),
            self._sample(
                source="SAMPLE troubleshooting note",
                source_type="sample_manual",
                modality="text",
                page=3120,
                title="Communication fault and LED troubleshooting",
                manual_title="S7-1500 diagnostics guide",
                module_model="CPU / PROFINET device",
                parameter="communication LED alarm",
                text=(
                    "For CPU or PROFINET communication faults, record LED state, alarm diagnostics, device "
                    "name, IP address, connection state, power state and recent configuration changes."
                ),
            ),
            self._sample(
                source="SafePLC offline industrial operation boundary",
                source_type="system_boundary",
                retrieval_backend="system_boundary",
                modality="policy",
                title="OFFLINE READ-ONLY operation boundary",
                manual_title="SafePLC Assist Box policy",
                module_model="SafePLC-Assist Box",
                parameter="industrial operation boundary",
                direct_evidence=True,
                text=(
                    "The assistant is offline and read-only. It must refuse requests to short circuits, "
                    "bypass protective functions, wire live equipment, force outputs, download to PLCs, "
                    "or control real PLC devices. It may suggest stop, isolation and qualified review."
                ),
            ),
            self._sample(
                source="SAMPLE S7-1500R/H redundant system manual",
                source_type="sample_manual",
                modality="figure",
                page=533,
                figure_id="fig_redundant_x1_decoy",
                figure_number="Figure R/H-35",
                title="S7-1500R/H redundant CPU interface",
                manual_title="S7-1500R/H redundant system manual",
                device_family="S7-1500R/H",
                module_model="CPU 1517H",
                parameter="X1 redundant interface",
                text="S7-1500R/H redundant CPU interface page. This is not CPU 1517-3 PN/DP evidence.",
            ),
        ]

    def _clone(self, ev: AgentEvidence) -> AgentEvidence:
        return AgentEvidence(
            evidence_id=ev.evidence_id,
            source=ev.source,
            source_type=ev.source_type,
            retrieval_backend=ev.retrieval_backend,
            modality=ev.modality,
            text=ev.text,
            compact_excerpt=ev.compact_excerpt,
            manual_title=ev.manual_title,
            manual_version=ev.manual_version,
            device_family=ev.device_family,
            module_model=ev.module_model,
            order_number=ev.order_number,
            page=ev.page,
            section=ev.section,
            figure_id=ev.figure_id,
            figure_number=ev.figure_number,
            image_path=ev.image_path,
            chunk_id=ev.chunk_id,
            document_id=ev.document_id,
            collection_name=ev.collection_name,
            query_text=ev.query_text,
            source_path=ev.source_path,
            retrieval_score=ev.retrieval_score,
            raw_distance=ev.raw_distance,
            normalized_score=ev.normalized_score,
            model_match_level=ev.model_match_level,
            direct_evidence=ev.direct_evidence,
            quality_score=ev.quality_score,
            title=ev.title,
            module=ev.module,
            parameter=ev.parameter,
            agent_names=list(ev.agent_names),
            claim_links=list(ev.claim_links),
            conflict_with=list(ev.conflict_with),
            metadata=dict(ev.metadata or {}),
        )
