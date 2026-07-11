#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Dict, List, Optional

from ..schemas import AgentEvidence
from .tool_registry import ToolRegistry


def search_hybrid(
    registry: ToolRegistry,
    query: str,
    modalities: Optional[List[str]] = None,
    filters: Optional[Dict[str, str]] = None,
    top_k: int = 4,
) -> List[AgentEvidence]:
    return registry.search_hybrid(
        query=query,
        modalities=modalities,
        filters=filters,
        top_k=top_k,
    )
