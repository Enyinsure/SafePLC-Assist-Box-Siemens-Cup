#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


VALID_MODES = {"FULL", "SAMPLE", "MOCK"}
VALID_ROUTING_STRATEGIES = {"adaptive", "single_best", "top_k", "static", "all_agents"}


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class SafePLCConfig:
    mode: str
    chroma_dir: str
    text_collection: str
    figure_chroma_dir: str
    figure_collection: str
    chunks_jsonl: str
    pages_jsonl: str
    figure_cards_jsonl: str
    figure_chunks_jsonl: str
    visual_dir: str
    model_path: str
    report_dir: str
    agent_timeout: int
    max_agents: int
    routing_strategy: str
    allow_jsonl_fallback: bool
    enable_jsonl_hybrid: bool
    jsonl_fallback_min_score: float
    require_figure_backend: bool
    embedding_backend: str
    embedding_model_path: str
    embedding_device: str
    embedding_normalize: bool
    embedding_query_prefix: str
    allow_chroma_default_embedding: bool
    allow_remote_model_download: bool
    enable_query_expansion: bool
    max_expanded_queries: int
    package_root: Path
    project_root: Path

    @classmethod
    def from_env(
        cls,
        mode: Optional[str] = None,
        routing_strategy: Optional[str] = None,
        max_agents: Optional[int] = None,
    ) -> "SafePLCConfig":
        package_root = Path(__file__).resolve().parent
        project_root = package_root.parent

        resolved_mode = (mode or os.environ.get("SAFEPLC_MODE", "SAMPLE")).strip().upper()
        if resolved_mode not in VALID_MODES:
            resolved_mode = "SAMPLE"

        resolved_strategy = (
            routing_strategy
            or os.environ.get("SAFEPLC_ROUTING_STRATEGY", "adaptive")
        ).strip()
        if resolved_strategy not in VALID_ROUTING_STRATEGIES:
            resolved_strategy = "adaptive"

        resolved_max_agents = max_agents
        if resolved_max_agents is None:
            try:
                resolved_max_agents = int(os.environ.get("SAFEPLC_MAX_AGENTS", "4"))
            except ValueError:
                resolved_max_agents = 4
        resolved_max_agents = max(1, min(int(resolved_max_agents), 8))

        try:
            timeout = int(os.environ.get("SAFEPLC_AGENT_TIMEOUT", "30"))
        except ValueError:
            timeout = 30
        try:
            fallback_min_score = float(os.environ.get("SAFEPLC_JSONL_FALLBACK_MIN_SCORE", "0.20"))
        except ValueError:
            fallback_min_score = 0.20
        try:
            max_expanded_queries = int(os.environ.get("SAFEPLC_MAX_EXPANDED_QUERIES", "2"))
        except ValueError:
            max_expanded_queries = 2

        return cls(
            mode=resolved_mode,
            chroma_dir=os.environ.get("SAFEPLC_CHROMA_DIR", ""),
            text_collection=os.environ.get("SAFEPLC_TEXT_COLLECTION", ""),
            figure_chroma_dir=os.environ.get("SAFEPLC_FIGURE_CHROMA_DIR", ""),
            figure_collection=os.environ.get("SAFEPLC_FIGURE_COLLECTION", ""),
            chunks_jsonl=os.environ.get("SAFEPLC_CHUNKS_JSONL", ""),
            pages_jsonl=os.environ.get("SAFEPLC_PAGES_JSONL", ""),
            figure_cards_jsonl=os.environ.get("SAFEPLC_FIGURE_CARDS_JSONL", ""),
            figure_chunks_jsonl=os.environ.get("SAFEPLC_FIGURE_CHUNKS_JSONL", ""),
            visual_dir=os.environ.get("SAFEPLC_VISUAL_DIR", ""),
            model_path=os.environ.get("SAFEPLC_MODEL_PATH", ""),
            report_dir=os.environ.get("SAFEPLC_REPORT_DIR", str(project_root / "reports")),
            agent_timeout=max(1, timeout),
            max_agents=resolved_max_agents,
            routing_strategy=resolved_strategy,
            allow_jsonl_fallback=_bool_env("SAFEPLC_ALLOW_JSONL_FALLBACK", False),
            enable_jsonl_hybrid=_bool_env("SAFEPLC_ENABLE_JSONL_HYBRID", False),
            jsonl_fallback_min_score=max(0.0, fallback_min_score),
            require_figure_backend=_bool_env("SAFEPLC_REQUIRE_FIGURE_BACKEND", False),
            embedding_backend=os.environ.get("SAFEPLC_EMBEDDING_BACKEND", "auto").strip().lower(),
            embedding_model_path=os.environ.get("SAFEPLC_EMBEDDING_MODEL_PATH", ""),
            embedding_device=os.environ.get("SAFEPLC_EMBEDDING_DEVICE", "cpu").strip() or "cpu",
            embedding_normalize=_bool_env("SAFEPLC_EMBEDDING_NORMALIZE", True),
            embedding_query_prefix=os.environ.get("SAFEPLC_EMBEDDING_QUERY_PREFIX", ""),
            allow_chroma_default_embedding=_bool_env("SAFEPLC_ALLOW_CHROMA_DEFAULT_EMBEDDING", False),
            allow_remote_model_download=_bool_env("SAFEPLC_ALLOW_REMOTE_MODEL_DOWNLOAD", False),
            enable_query_expansion=_bool_env("SAFEPLC_ENABLE_QUERY_EXPANSION", True),
            max_expanded_queries=max(0, min(max_expanded_queries, 2)),
            package_root=package_root,
            project_root=project_root,
        )

    def path_status(self) -> Dict[str, bool]:
        paths = {
            "SAFEPLC_CHROMA_DIR": self.chroma_dir,
            "SAFEPLC_FIGURE_CHROMA_DIR": self.figure_chroma_dir,
            "SAFEPLC_CHUNKS_JSONL": self.chunks_jsonl,
            "SAFEPLC_PAGES_JSONL": self.pages_jsonl,
            "SAFEPLC_FIGURE_CARDS_JSONL": self.figure_cards_jsonl,
            "SAFEPLC_FIGURE_CHUNKS_JSONL": self.figure_chunks_jsonl,
            "SAFEPLC_VISUAL_DIR": self.visual_dir,
        }
        return {name: bool(value and Path(value).exists()) for name, value in paths.items()}

    def missing_full_requirements(self) -> List[str]:
        status = self.path_status()
        missing: List[str] = []
        if not status.get("SAFEPLC_CHROMA_DIR"):
            missing.append("SAFEPLC_CHROMA_DIR")
        if not status.get("SAFEPLC_FIGURE_CHROMA_DIR") and self.require_figure_backend:
            missing.append("SAFEPLC_FIGURE_CHROMA_DIR")
        if self.allow_jsonl_fallback:
            if not status.get("SAFEPLC_CHUNKS_JSONL"):
                missing.append("SAFEPLC_CHUNKS_JSONL")
            if not status.get("SAFEPLC_PAGES_JSONL"):
                missing.append("SAFEPLC_PAGES_JSONL")
        return missing

    def full_assets_available(self) -> bool:
        if self.mode != "FULL":
            return True
        if self.chroma_dir and Path(self.chroma_dir).exists():
            return True
        if self.allow_jsonl_fallback and self.chunks_jsonl and Path(self.chunks_jsonl).exists():
            return True
        return False
