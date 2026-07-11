#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from ..schemas import AgentEvidence
from .metadata_normalizer import first_value, load_jsonl_records, normalize_metadata


_CACHE: Dict[str, List[Tuple[str, Dict[str, object]]]] = {}


def tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_/\-]*|[\u4e00-\u9fff]{2,}", text or "")
    return list(dict.fromkeys(t.lower() for t in tokens if t.strip()))


class JSONLFallbackRetriever:
    def __init__(self, paths: Sequence[str], backend: str, modality_hint: str = "text") -> None:
        self.paths = [Path(p) for p in paths if p]
        self.backend = backend
        self.modality_hint = modality_hint
        self.last_latency_ms = 0

    def available(self) -> bool:
        return any(path.exists() for path in self.paths)

    def line_count(self) -> int:
        return sum(len(self._load(path)) for path in self.paths if path.exists())

    def search(
        self,
        query: str,
        top_k: int = 8,
        modalities: Optional[Iterable[str]] = None,
    ) -> List[AgentEvidence]:
        started = time.perf_counter()
        allowed = {m.lower() for m in modalities or []}
        q_tokens = tokenize(query)
        scored: List[Tuple[float, AgentEvidence]] = []
        for path in self.paths:
            if not path.exists():
                continue
            for text, meta in self._load(path):
                modality = str(meta.get("modality") or meta.get("source_type") or self.modality_hint).lower()
                if allowed and modality not in allowed:
                    continue
                score = self._lexical_score(q_tokens, text, meta)
                if score <= 0:
                    continue
                meta = dict(meta)
                meta.setdefault("source_path", str(path))
                meta.setdefault("chunk_id", first_value(meta, ("chunk_id", "id", "uid"), f"{path.name}:{meta.get('_line_no', '')}"))
                ev = normalize_metadata(
                    text=text,
                    metadata=meta,
                    backend=self.backend,
                    query_text=query,
                    source_path=str(path),
                    fallback_score=score,
                    modality_hint=modality or self.modality_hint,
                )
                scored.append((score, ev))
        scored.sort(key=lambda item: item[0], reverse=True)
        self.last_latency_ms = int((time.perf_counter() - started) * 1000)
        return [ev for _, ev in scored[: max(1, top_k)]]

    def _load(self, path: Path) -> List[Tuple[str, Dict[str, object]]]:
        key = str(path.resolve())
        if key in _CACHE:
            return _CACHE[key]
        rows: List[Tuple[str, Dict[str, object]]] = []
        for record in load_jsonl_records(path):
            text = first_value(record, ("text", "content", "chunk", "document", "ocr_text", "caption"))
            if not text.strip():
                continue
            rows.append((text, record))
        _CACHE[key] = rows
        return rows

    def _lexical_score(self, q_tokens: List[str], text: str, meta: Dict[str, object]) -> float:
        haystack = " ".join([text, " ".join(str(v) for v in meta.values())]).lower()
        if not q_tokens:
            return 0.0
        hits = sum(1 for token in q_tokens if token in haystack)
        if hits == 0:
            return 0.0
        coverage = hits / max(len(q_tokens), 1)
        direct = 0.2 if any(k in haystack for k in ("x1", "profinet", "1517", "6es7517")) else 0.0
        return round(min(1.0, coverage + direct), 6)
