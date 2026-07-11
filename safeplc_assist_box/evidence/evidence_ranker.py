#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Iterable, List

from ..schemas import AgentEvidence


def rank_evidence(evidences: Iterable[AgentEvidence]) -> List[AgentEvidence]:
    return sorted(
        list(evidences),
        key=lambda ev: (
            ev.retrieval_score,
            1 if ev.page is not None else 0,
            1 if ev.figure_id else 0,
            len(ev.text or ""),
        ),
        reverse=True,
    )

