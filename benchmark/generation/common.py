from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Sequence, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_CASES_PATH = PROJECT_ROOT / "benchmark" / "full_core_30" / "cases.jsonl"
FULL_360_DIR = PROJECT_ROOT / "benchmark" / "cases" / "full_360"
SCHEMA_PATH = PROJECT_ROOT / "benchmark" / "schemas" / "full_360_case.schema.json"
SCHEMA_VERSION = "safeplc.full_360.case.v1"
GENERATOR_SEED = 42

NATURAL_COUNTS = {
    "parameter": 36,
    "wiring": 36,
    "troubleshooting": 36,
    "figure_location": 36,
    "topology_clarification": 24,
    "emc": 24,
    "compound_multi_agent": 24,
    "missing_slot_clarification": 12,
    "maintenance_work_order": 12,
}

STRESS_COUNTS = {
    "cross_model_contamination": 24,
    "unsupported_entity": 24,
    "industrial_safety_refusal": 18,
    "conflicting_or_distractor_evidence": 12,
    "multimodal_missing_or_mismatch": 12,
}

LAYER_COUNTS = {"core": 30, "natural": 240, "stress": 90}


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"JSONL object required at {path}:{line_number}")
            records.append(value)
    return records


def write_jsonl(path: Path, records: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    temporary.replace(path)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_query(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", text, flags=re.UNICODE)


def query_tokens(value: str) -> set[str]:
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    latin = re.findall(r"[a-z0-9]+(?:[-/][a-z0-9]+)*", text)
    chinese = re.findall(r"[\u4e00-\u9fff]", text)
    return set(latin + chinese)


def character_ngrams(value: str, size: int = 3) -> set[str]:
    normalized = normalize_query(value)
    if len(normalized) <= size:
        return {normalized} if normalized else set()
    return {normalized[index:index + size] for index in range(len(normalized) - size + 1)}


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def near_duplicate_candidates(
    cases: Sequence[Dict[str, Any]],
    *,
    token_threshold: float = 0.88,
    trigram_threshold: float = 0.90,
) -> List[Dict[str, Any]]:
    prepared = [
        (
            str(case.get("case_id") or ""),
            str(case.get("query") or ""),
            query_tokens(str(case.get("query") or "")),
            character_ngrams(str(case.get("query") or "")),
        )
        for case in cases
    ]
    candidates: List[Dict[str, Any]] = []
    for left_index, left in enumerate(prepared):
        for right in prepared[left_index + 1:]:
            token_score = jaccard(left[2], right[2])
            trigram_score = jaccard(left[3], right[3])
            if token_score < token_threshold and trigram_score < trigram_threshold:
                continue
            candidates.append({
                "left_case_id": left[0],
                "right_case_id": right[0],
                "token_jaccard": round(token_score, 6),
                "character_3gram_jaccard": round(trigram_score, 6),
                "review_status": "pending",
            })
    return candidates


def category_counts(cases: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    return dict(Counter(str(case.get("category") or "") for case in cases))


def layer_for_case(case: Dict[str, Any]) -> str:
    return str(case.get("benchmark_layer") or "core")


def chunked(values: Sequence[Any], size: int) -> Iterator[Sequence[Any]]:
    for index in range(0, len(values), size):
        yield values[index:index + size]


def forbidden_project_terms() -> Tuple[str, ...]:
    # Keep the benchmark domain clean while avoiding those unrelated labels in docs/data.
    return (
        "prompt" + " injection",
        "retrieval" + " poisoning",
        "M" + "-EPI",
        "S" + "M2",
        "S" + "M3",
        "S" + "M4",
        "trusted" + "_rag",
        "sec" + "guard",
    )
