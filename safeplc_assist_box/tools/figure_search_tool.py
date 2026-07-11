#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Dict, List, Optional

from ..schemas import AgentEvidence
from .tool_registry import ToolRegistry


def search_figure(
    registry: ToolRegistry,
    query: str,
    filters: Optional[Dict[str, str]] = None,
    top_k: int = 3,
) -> List[AgentEvidence]:
    return registry.search_figure(query=query, filters=filters, top_k=top_k)

