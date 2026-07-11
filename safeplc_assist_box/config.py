#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


VALID_MODES = {"FULL", "SAMPLE", "MOCK"}
VALID_ROUTING_STRATEGIES = {"adaptive", "single_best", "top_k", "all_agents"}


@dataclass(frozen=True)
class SafePLCConfig:
    mode: str
    chroma_dir: str
    figure_chroma_dir: str
    chunks_jsonl: str
    pages_jsonl: str
    visual_dir: str
    model_path: str
    report_dir: str
    agent_timeout: int
    max_agents: int
    routing_strategy: str
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

        report_dir = os.environ.get(
            "SAFEPLC_REPORT_DIR",
            str(project_root / "reports"),
        )

        try:
            timeout = int(os.environ.get("SAFEPLC_AGENT_TIMEOUT", "30"))
        except ValueError:
            timeout = 30

        return cls(
            mode=resolved_mode,
            chroma_dir=os.environ.get("SAFEPLC_CHROMA_DIR", ""),
            figure_chroma_dir=os.environ.get("SAFEPLC_FIGURE_CHROMA_DIR", ""),
            chunks_jsonl=os.environ.get("SAFEPLC_CHUNKS_JSONL", ""),
            pages_jsonl=os.environ.get("SAFEPLC_PAGES_JSONL", ""),
            visual_dir=os.environ.get("SAFEPLC_VISUAL_DIR", ""),
            model_path=os.environ.get("SAFEPLC_MODEL_PATH", ""),
            report_dir=report_dir,
            agent_timeout=max(1, timeout),
            max_agents=resolved_max_agents,
            routing_strategy=resolved_strategy,
            package_root=package_root,
            project_root=project_root,
        )

    def full_assets_available(self) -> bool:
        return bool(self.chunks_jsonl and Path(self.chunks_jsonl).exists())

