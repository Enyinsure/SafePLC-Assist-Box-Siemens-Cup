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
from ..retrieval.query_expander import QueryExpander
from .chroma_figure_retriever import ChromaFigureRetriever
from .chroma_text_retriever import ChromaTextRetriever
from .embedding_adapter import EmbeddingAdapter
from .jsonl_fallback_retriever import JSONLFallbackRetriever
from .metadata_normalizer import normalize_metadata
from .verified_figure_catalog import enrich_verified_figure_evidence


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
            "jsonl_fallback_triggered": False,
            "jsonl_fallback_reason": "",
            "hybrid_mode": config.enable_jsonl_hybrid,
            "tool_calls": [],
            "sample_fixture_active": config.mode != "FULL",
            "errors": self.errors,
        }
        self._sample_evidence = self._build_sample_evidence() if config.mode != "FULL" else []
        self._text_retriever: Optional[ChromaTextRetriever] = None
        self._figure_retriever: Optional[ChromaFigureRetriever] = None
        self._jsonl_chunks: Optional[JSONLFallbackRetriever] = None
        self._jsonl_pages: Optional[JSONLFallbackRetriever] = None
        self._figure_jsonl: Optional[JSONLFallbackRetriever] = None
        self._evidence_cache_by_id: Dict[str, AgentEvidence] = {}
        self._evidence_cache_by_page: Dict[str, List[AgentEvidence]] = {}
        self._evidence_cache_by_figure: Dict[str, List[AgentEvidence]] = {}
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
        return self._search(query, {"figure", "visual", "text"}, filters=filters, top_k=top_k, tool="search_figure")

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
        started = time.perf_counter()
        self.tool_call_count += 1
        candidates = list(self._evidence_cache_by_page.get(str(page_id), []))
        if self.config.mode != "FULL":
            candidates.extend(ev for ev in self._sample_evidence if str(ev.page or "") == str(page_id))
        result = self._best_cached(candidates)
        self._record_tool_call(
            "fetch_page", str(page_id), set(), [result] if result else [], started,
            backend_attempted=["retrieval_cache"], backend_used=["retrieval_cache"] if result else [],
        )
        return result

    def fetch_figure(self, figure_id: str) -> Optional[AgentEvidence]:
        started = time.perf_counter()
        self.tool_call_count += 1
        candidates = list(self._evidence_cache_by_figure.get(str(figure_id), []))
        if self.config.mode != "FULL":
            candidates.extend(
                ev for ev in self._sample_evidence if ev.figure_id == figure_id or ev.figure_number == figure_id
            )
        result = self._best_cached(candidates)
        self._record_tool_call(
            "fetch_figure", str(figure_id), {"figure"}, [result] if result else [], started,
            backend_attempted=["retrieval_cache"], backend_used=["retrieval_cache"] if result else [],
        )
        return result

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
            self.backend_audit["jsonl_fallback_available"] = any(
                r and r.available() for r in [self._jsonl_chunks, self._jsonl_pages, self._figure_jsonl]
            )

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
            expansion = QueryExpander().expand(
                query,
                max_expanded_queries=self.config.max_expanded_queries if self.config.enable_query_expansion else 0,
            )
            records, call_details = self._search_full(
                query, expansion.all_queries, expansion.expansion_reasons, allowed, top_k_per_query=max(12, top_k * 3)
            )
            call_details["expanded_queries"] = expansion.expanded_queries
        else:
            records = self._search_sample(query, allowed, filters=filters, top_k=max(top_k, 8), tool=tool)
            call_details = {
                "backend_attempted": ["sample_fixture"],
                "backend_used": ["sample_fixture"] if records else [],
                "fallback_reason": "",
                "error": "",
            }
        if self.feature_switches.get("enable_figure_backend", True):
            records = [enrich_verified_figure_evidence(ev) for ev in records]
        if self.config.mode != "FULL" and self.feature_switches.get("enable_model_filter", True):
            records = reject_cross_family(records, query)
        if self.feature_switches.get("enable_evidence_reranker", True):
            records = rank_evidence(
                records,
                query=query,
                required_modality="figure" if allowed & {"figure", "visual"} and not allowed & {"text", "table"} else None,
                top_k=top_k,
            )
        self.last_latency_ms = int((time.perf_counter() - started) * 1000)
        records = records[: max(1, top_k)]
        self._cache_evidence(records)
        self._record_tool_call(
            tool,
            query,
            allowed,
            records,
            started,
            backend_attempted=call_details["backend_attempted"],
            backend_used=call_details["backend_used"],
            fallback_reason=str(call_details.get("fallback_reason") or ""),
            error=str(call_details.get("error") or ""),
            expanded_queries=list(call_details.get("expanded_queries") or []),
        )
        return records

    def _search_full(
        self,
        query: str,
        retrieval_queries: List[str],
        expansion_reasons: List[str],
        allowed: Set[str],
        top_k_per_query: int,
    ):
        chroma_records: List[AgentEvidence] = []
        jsonl_records: List[AgentEvidence] = []
        need_text = bool(allowed & {"text", "table", "policy"})
        need_figure = bool(allowed & {"figure", "visual"})
        exact_figure_match = False
        attempted: List[str] = []
        used: List[str] = []
        errors: List[str] = []
        backend_missing = False

        if need_figure and self._figure_retriever:
            attempted.append("chroma_figure")
            try:
                found = self._figure_retriever.search(query, top_k=top_k_per_query)
                chroma_records.extend(found)
                exact_figure_match = any(
                    bool((ev.metadata or {}).get("exact_page_match"))
                    for ev in found
                )
                if found:
                    used.append("chroma_figure")
            except Exception as exc:
                self.errors.append(str(exc))
                errors.append(str(exc))
        elif need_figure:
            backend_missing = True

        # An explicitly requested page resolved to a real figure card.
        # Do not launch the expensive and potentially distracting text search.
        if exact_figure_match:
            need_text = False

        if need_text and self._text_retriever:
            attempted.append("chroma_text")
            try:
                search_many = getattr(self._text_retriever, "search_many", None)
                found = search_many(
                    retrieval_queries, top_k_per_query=top_k_per_query, expansion_reasons=expansion_reasons
                ) if callable(search_many) else self._text_retriever.search(query, top_k=top_k_per_query)
                chroma_records.extend(found)
                if found:
                    used.append("chroma_text")
            except Exception as exc:
                self.errors.append(str(exc))
                errors.append(str(exc))
        elif need_text:
            backend_missing = True

        before_filter = len(chroma_records)
        if self.feature_switches.get("enable_model_filter", True):
            chroma_records = reject_cross_family(chroma_records, query)
        after_filter = len(chroma_records)
        best_score = max(
            (float(ev.normalized_score or ev.retrieval_score or 0.0) for ev in chroma_records),
            default=0.0,
        )
        figure_hit = any(
            ev.modality in {"figure", "visual"}
            or ev.manual_figure_number
            or bool(re.search(r"(?:前视图|front view|接口位置)", ev.text or "", re.I))
            for ev in chroma_records
        )
        reasons: List[str] = []
        if not attempted:
            reasons.append("backend_not_configured")
        elif backend_missing:
            reasons.append("requested_modality_backend_unavailable")
        if errors:
            reasons.append("backend_query_failed")
        if before_filter == 0:
            reasons.append("backend_zero_results:chroma_returned_zero")
        elif after_filter == 0:
            reasons.append("all_candidates_rejected_by_model_filter")
        if after_filter and best_score < self.config.jsonl_fallback_min_score:
            reasons.append("all_candidates_rejected_by_score:below_threshold")
        if need_figure and not figure_hit:
            reasons.append("required_figure_evidence_missing")

        trigger_fallback = bool(reasons)
        query_jsonl = self.config.allow_jsonl_fallback and (
            self.config.enable_jsonl_hybrid or trigger_fallback
        )

        if query_jsonl:
            if need_figure and self._figure_jsonl and self._figure_jsonl.available():
                attempted.append("jsonl_figure")
                found = self._figure_jsonl.search(query, top_k=top_k_per_query, modalities=allowed)
                jsonl_records.extend(found)
                if found:
                    used.append("jsonl_figure")
            if need_text and self._jsonl_chunks and self._jsonl_chunks.available():
                attempted.append("jsonl_chunks")
                found = self._jsonl_chunks.search(query, top_k=top_k_per_query, modalities=allowed)
                jsonl_records.extend(found)
                if found:
                    used.append("jsonl_chunks")
            if need_text and self._jsonl_pages and self._jsonl_pages.available():
                attempted.append("jsonl_pages")
                found = self._jsonl_pages.search(query, top_k=top_k_per_query, modalities=allowed)
                jsonl_records.extend(found)
                if found:
                    used.append("jsonl_pages")

        if query_jsonl and self.feature_switches.get("enable_model_filter", True):
            jsonl_records = reject_cross_family(jsonl_records, query)
        fallback_reason = ",".join(reasons) if trigger_fallback else ("explicit_hybrid_mode" if query_jsonl else "")
        self.backend_audit.update(
            {
                "jsonl_fallback_active": bool(query_jsonl),
                "jsonl_fallback_triggered": bool(query_jsonl and trigger_fallback),
                "jsonl_fallback_reason": fallback_reason,
                "chroma_result_count_before_filter": before_filter,
                "chroma_result_count_after_filter": after_filter,
                "chroma_best_score": best_score,
                "jsonl_result_count": len(jsonl_records),
                "hybrid_mode": self.config.enable_jsonl_hybrid,
                "retrieval_queries": retrieval_queries,
                "candidate_count_before_final_ranking": len(chroma_records) + len(jsonl_records),
                "backend_attempted": list(dict.fromkeys(attempted)),
                "backend_used": list(dict.fromkeys(used)),
                "raw_result_count": before_filter,
                "post_model_filter_count": after_filter,
                "rejection_counts_by_reason": {
                    "model_filter": max(0, before_filter - after_filter),
                    "score": after_filter if after_filter and best_score < self.config.jsonl_fallback_min_score else 0,
                },
            }
        )
        if not chroma_records and not jsonl_records and not self.config.allow_jsonl_fallback:
            if not attempted:
                self.errors.append("FULL retrieval backend_not_configured for requested modalities.")
            elif errors:
                self.errors.append("FULL retrieval backend_query_failed; inspect backend audit errors.")
            elif before_filter == 0:
                self.errors.append("FULL retrieval backend_zero_results.")
            elif after_filter == 0:
                self.errors.append("FULL retrieval all_candidates_rejected_by_model_filter.")
        records = chroma_records + jsonl_records if query_jsonl else chroma_records
        return records, {
            "backend_attempted": attempted,
            "backend_used": used,
            "fallback_reason": fallback_reason,
            "error": "; ".join(errors),
        }

    def _cache_evidence(self, records: List[AgentEvidence]) -> None:
        for ev in records:
            self._evidence_cache_by_id[ev.evidence_id] = ev
            if ev.page is not None:
                self._evidence_cache_by_page.setdefault(str(ev.page), []).append(ev)
            for key in (ev.figure_id, ev.figure_number):
                if key:
                    self._evidence_cache_by_figure.setdefault(str(key), []).append(ev)

    def _best_cached(self, records: List[AgentEvidence]) -> Optional[AgentEvidence]:
        if not records:
            return None
        return max(records, key=lambda ev: (ev.quality_score, ev.normalized_score, ev.retrieval_score))

    def _record_tool_call(
        self,
        tool: str,
        query: str,
        modalities: Set[str],
        records: List[AgentEvidence],
        started: float,
        backend_attempted: List[str],
        backend_used: List[str],
        fallback_reason: str = "",
        error: str = "",
        expanded_queries: Optional[List[str]] = None,
    ) -> None:
        calls = self.backend_audit.setdefault("tool_calls", [])
        assert isinstance(calls, list)
        calls.append(
            {
                "tool": tool,
                "query": query,
                "requested_modalities": sorted(modalities),
                "backend_attempted": list(dict.fromkeys(backend_attempted)),
                "backend_used": list(dict.fromkeys(backend_used)),
                "result_count": len(records),
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "fallback_reason": fallback_reason,
                "error": error,
                "expanded_queries": list(expanded_queries or []),
            }
        )

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
        if self.feature_switches.get("enable_figure_backend", True):
            ev = enrich_verified_figure_evidence(ev)
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
                manual_title="CPU 1517-3 PN/DP 设备手册",
                manual_version="11/2023",
                document_id="A5E33595080-AF",
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
                    "端子接线应设置电源隔离设备，使用 SELV/PELV 电源并连接保护性导线；"
                    "核对极性、线径和额定电压范围。"
                ),
            ),
            self._sample(
                source="SAMPLE EMC installation note",
                source_type="sample_manual",
                modality="text",
                page=6495,
                title="EMC grounding and shielding",
                manual_title="S7-1500 / ET 200MP manual",
                module_model="S7-1500 / ET 200MP",
                parameter="EMC grounding shielding cable layout",
                text=(
                    "The system is intended for industrial environment use. For residential environments it must meet EN 55011 Class B. "
                    "Measures include grounded control cabinets/control boxes and noise filters in supply lines."
                ),
            ),
            self._sample(
                source="SAMPLE troubleshooting note",
                source_type="sample_manual",
                modality="text",
                page=2482,
                title="Communication fault and LED troubleshooting",
                manual_title="CPU 1517-3 PN/DP 设备手册",
                manual_version="11/2023",
                document_id="A5E33595080-AF",
                module_model="CPU 1517-3 PN/DP",
                order_number="6ES7517-3AP00-0AB0",
                figure_id="fig_cpu1517_3pn_led_2_240",
                figure_number="Figure 2-240",
                parameter="communication LED alarm",
                direct_evidence=True,
                text=(
                    "RUN/STOP LED, ERROR LED, MAINT LED, X1 P1 LINK RX/TX LED, "
                    "X1 P2 LINK RX/TX LED and X2 P1 LINK RX/TX LED. Figure 2-240."
                ),
            ),
            self._sample(
                source="SAMPLE S7-1500R/H topology example",
                source_type="sample_manual",
                modality="text",
                page=1531,
                title="S7-1500R/H HMI PROFINET example",
                manual_title="S7-1500R/H redundant system manual",
                device_family="S7-1500R/H",
                module_model="S7-1500R/H",
                parameter="HMI CPU PROFINET relationship",
                direct_evidence=True,
                text="In this S7-1500R/H example, HMI PROFINET X1 connects to the R/H CPU PROFINET X2.",
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
            visual_record_id=ev.visual_record_id,
            manual_figure_number=ev.manual_figure_number,
            manual_figure_caption=ev.manual_figure_caption,
            image_path=ev.image_path,
            raw_image_path=ev.raw_image_path,
            resolved_image_path=ev.resolved_image_path,
            image_exists=ev.image_exists,
            visual_evidence_status=ev.visual_evidence_status,
            chunk_id=ev.chunk_id,
            document_id=ev.document_id,
            collection_name=ev.collection_name,
            query_text=ev.query_text,
            retrieval_query=ev.retrieval_query,
            retrieval_query_index=ev.retrieval_query_index,
            query_expansion_reason=ev.query_expansion_reason,
            rank_within_query=ev.rank_within_query,
            query_ranks=dict(ev.query_ranks),
            rrf_score=ev.rrf_score,
            matched_query_count=ev.matched_query_count,
            best_query_rank=ev.best_query_rank,
            source_path=ev.source_path,
            retrieval_score=ev.retrieval_score,
            raw_distance=ev.raw_distance,
            normalized_score=ev.normalized_score,
            distance_metric=ev.distance_metric,
            score_conversion=ev.score_conversion,
            vector_similarity=ev.vector_similarity,
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
