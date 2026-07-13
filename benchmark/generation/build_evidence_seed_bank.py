#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from benchmark.generation.common import FULL_360_DIR, stable_hash, write_json, write_jsonl
from safeplc_assist_box.evidence.fact_extractors import (
    extract_emc_facts,
    extract_led_checks,
    extract_parameter_facts,
    extract_topology_fact,
    extract_wiring_facts,
)
from safeplc_assist_box.tools.metadata_normalizer import (
    extract_location_markers,
    extract_manual_figure,
    normalize_metadata,
)


DEFAULT_SEED_PATH = FULL_360_DIR / "evidence_seed_bank.jsonl"
DEFAULT_REPORT_PATH = FULL_360_DIR / "evidence_seed_bank_report.json"
SOURCE_ENV = {
    "SAFEPLC_CHUNKS_JSONL": "jsonl_metadata",
    "SAFEPLC_PAGES_JSONL": "jsonl_metadata",
    "SAFEPLC_FIGURE_CARDS_JSONL": "jsonl_metadata",
    "SAFEPLC_FIGURE_CHUNKS_JSONL": "jsonl_metadata",
}


class AssetUnavailableError(RuntimeError):
    pass


def _text_from_record(record: Dict[str, Any]) -> str:
    for key in ("text", "content", "chunk", "document", "ocr_text", "caption", "page_text"):
        value = record.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def _metadata_from_record(record: Dict[str, Any]) -> Dict[str, Any]:
    nested = record.get("metadata")
    metadata = dict(nested) if isinstance(nested, dict) else {}
    for key, value in record.items():
        if key not in {"metadata", "text", "content", "chunk", "document", "ocr_text", "page_text"}:
            metadata.setdefault(key, value)
    return metadata


def _quality_rejection(text: str) -> str:
    value = unicodedata.normalize("NFKC", str(text or "")).strip()
    if len(value) < 24:
        return "empty_or_too_short"
    if value.count("\ufffd") > 0 or sum(value.count(token) for token in ("锛", "鈶", "妯", "鐨")) >= 3:
        return "garbled_text"
    visible = [char for char in value if not char.isspace()]
    useful = [char for char in visible if char.isalnum() or "\u4e00" <= char <= "\u9fff"]
    if not visible or len(useful) / len(visible) < 0.45:
        return "low_information_text"
    lower = value.lower()
    if any(term in lower for term in ("table of contents", "目录 ........", "索引 ........")):
        return "directory_or_index_page"
    if len(re.findall(r"\.{5,}|…{3,}", value)) >= 3:
        return "directory_or_index_page"
    return ""


def _port_facts(text: str) -> List[Dict[str, Any]]:
    facts: List[Dict[str, Any]] = []
    pattern = re.compile(
        r"\b(?P<interface>X\d+)\b[^。；;\n]{0,70}?(?P<count>\d+)\s*(?:个\s*)?(?:端口|ports?)",
        re.I,
    )
    for match in pattern.finditer(text):
        facts.append({"interface": match.group("interface").upper(), "port_count": int(match.group("count"))})
    return facts


def extract_structured_facts(text: str) -> Dict[str, Any]:
    facts: Dict[str, Any] = {}
    parameter = extract_parameter_facts(text)
    parameter_payload = asdict(parameter)
    parameter_payload.pop("evidence_span", None)
    parameter_payload["complete"] = parameter.complete
    if parameter.rated_values or any(
        value is not None
        for value in (parameter.static_lower, parameter.static_upper, parameter.dynamic_lower, parameter.dynamic_upper)
    ):
        facts["parameter"] = parameter_payload

    interfaces = sorted(set(re.findall(r"\bX\d+\b", text, re.I)))
    if interfaces:
        facts["interfaces"] = [item.upper() for item in interfaces]
    ports = _port_facts(text)
    if ports:
        facts["ports"] = ports

    figure_number, figure_caption = extract_manual_figure(text)
    if figure_number:
        facts["figure"] = {"number": figure_number, "caption": figure_caption}
    markers = extract_location_markers(text)
    if markers:
        facts["location_markers"] = markers

    led_checks: Dict[str, List[str]] = {}
    for interface in interfaces or ["X1"]:
        checks = extract_led_checks(text, interface.upper())
        if checks:
            led_checks[interface.upper()] = checks
    if led_checks:
        facts["led_checks"] = led_checks

    wiring = extract_wiring_facts(text)
    if wiring:
        facts["wiring_requirements"] = wiring
    emc = extract_emc_facts(text)
    if emc:
        facts["emc_measures"] = emc
    topology = extract_topology_fact(text)
    if topology:
        facts["topology"] = topology
    return facts


def build_seed(
    record: Dict[str, Any],
    *,
    source_type: str,
    source_path: str,
    collection_name: str = "",
    record_id: str = "",
) -> Tuple[Optional[Dict[str, Any]], str]:
    text = _text_from_record(record)
    rejection = _quality_rejection(text)
    if rejection:
        return None, rejection
    metadata = _metadata_from_record(record)
    backend = "chroma_figure" if source_type == "figure_chroma" else "chroma_text"
    evidence = normalize_metadata(
        text=text,
        metadata=metadata,
        backend=backend,
        collection_name=collection_name,
        source_path=source_path,
        modality_hint="figure" if source_type == "figure_chroma" else "text",
    )
    structured = extract_structured_facts(text)
    if not structured and not any((evidence.module_model, evidence.order_number, evidence.section)):
        return None, "no_verifiable_fact"
    source_record_id = record_id or str(
        metadata.get("id") or metadata.get("chunk_id") or metadata.get("chunk_index") or metadata.get("figure_id") or ""
    )
    if not source_record_id:
        source_record_id = stable_hash({"source": evidence.source, "page": evidence.page, "text": text})[:20]
    seed_key = {
        "source_type": source_type,
        "source": evidence.source,
        "page": evidence.page,
        "record": source_record_id,
        "text": " ".join(text.split()),
    }
    modality = ["figure"] if source_type == "figure_chroma" else [str(evidence.modality or "text")]
    seed = {
        "seed_id": "seed_" + stable_hash(seed_key)[:16],
        "source_type": source_type,
        "manual_title": evidence.manual_title,
        "device_family": evidence.device_family,
        "module_model": evidence.module_model,
        "order_number": evidence.order_number,
        "page": int(evidence.page or 0),
        "section": evidence.section,
        "figure_id": evidence.manual_figure_number or evidence.figure_id,
        "modality": list(dict.fromkeys(modality)),
        "evidence_excerpt": " ".join(text.split())[:1200],
        "structured_facts": structured,
        "source_record_id": source_record_id,
        "source_verified": True,
        "source_path_env": _source_env_name(source_path),
        "collection_name": collection_name,
    }
    return seed, ""


def _source_env_name(source_path: str) -> str:
    resolved = str(Path(source_path).expanduser()) if source_path else ""
    for key in (
        "SAFEPLC_CHROMA_DIR", "SAFEPLC_FIGURE_CHROMA_DIR", *SOURCE_ENV.keys(),
    ):
        configured = os.environ.get(key, "")
        if configured and str(Path(configured).expanduser()) == resolved:
            return key
    return ""


def build_seed_bank_from_records(
    records: Iterable[Tuple[Dict[str, Any], str, str, str, str]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    seeds: List[Dict[str, Any]] = []
    rejected: Counter[str] = Counter()
    seen = set()
    source_counts: Counter[str] = Counter()
    for record, source_type, source_path, collection_name, record_id in records:
        seed, reason = build_seed(
            record,
            source_type=source_type,
            source_path=source_path,
            collection_name=collection_name,
            record_id=record_id,
        )
        if not seed:
            rejected[reason or "unknown"] += 1
            continue
        dedupe_key = stable_hash({
            "source": seed["source_path_env"],
            "manual": seed["manual_title"],
            "page": seed["page"],
            "excerpt": seed["evidence_excerpt"],
        })
        if dedupe_key in seen:
            rejected["duplicate"] += 1
            continue
        seen.add(dedupe_key)
        seeds.append(seed)
        source_counts[source_type] += 1
    fact_counts = Counter(
        fact_name
        for seed in seeds
        for fact_name in (seed.get("structured_facts") or {}).keys()
    )
    report = {
        "schema": "safeplc.full_360.seed_bank_report.v1",
        "status": "COMPLETE" if seeds else "BLOCKED",
        "seed_count": len(seeds),
        "source_type_counts": dict(sorted(source_counts.items())),
        "structured_fact_counts": dict(sorted(fact_counts.items())),
        "rejected_counts": dict(sorted(rejected.items())),
        "source_verified_count": sum(seed.get("source_verified") is True for seed in seeds),
    }
    return seeds, report


def _jsonl_records(path: Path, max_records: int = 0) -> Iterator[Tuple[Dict[str, Any], str, str, str, str]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        emitted = 0
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
            if not isinstance(value, dict):
                continue
            yield value, "jsonl_metadata", str(path), "", str(value.get("id") or line_number)
            emitted += 1
            if max_records and emitted >= max_records:
                return


def _select_chroma_collection(client: Any, requested: str, path: Path) -> Any:
    collections = list(client.list_collections())
    names = [str(getattr(item, "name", item)) for item in collections]
    if requested:
        if requested not in names:
            raise AssetUnavailableError(f"Configured collection {requested!r} not found in {path}")
        return client.get_collection(requested)
    if len(names) != 1:
        raise AssetUnavailableError(
            f"Exactly one collection or an explicit collection name is required for {path}; found {names}"
        )
    return client.get_collection(names[0])


def _chroma_records(
    path: Path,
    collection_name: str,
    source_type: str,
    max_records: int = 0,
) -> Iterator[Tuple[Dict[str, Any], str, str, str, str]]:
    try:
        import chromadb  # type: ignore
    except Exception as exc:
        raise AssetUnavailableError("chromadb is required to read configured Chroma assets") from exc
    client = chromadb.PersistentClient(path=str(path))
    collection = _select_chroma_collection(client, collection_name, path)
    selected_name = str(getattr(collection, "name", collection_name))
    total = int(collection.count())
    if max_records:
        total = min(total, max_records)
    batch_size = 500
    for offset in range(0, total, batch_size):
        raw = collection.get(
            limit=min(batch_size, total - offset),
            offset=offset,
            include=["documents", "metadatas"],
        )
        ids = raw.get("ids") or []
        documents = raw.get("documents") or []
        metadatas = raw.get("metadatas") or []
        for index, record_id in enumerate(ids):
            document = documents[index] if index < len(documents) else ""
            metadata = metadatas[index] if index < len(metadatas) and isinstance(metadatas[index], dict) else {}
            yield (
                {"text": str(document or ""), "metadata": metadata},
                source_type,
                str(path),
                selected_name,
                str(record_id),
            )


def configured_records(max_records_per_source: int = 0) -> Iterator[Tuple[Dict[str, Any], str, str, str, str]]:
    configured = 0
    text_path = Path(os.environ.get("SAFEPLC_CHROMA_DIR", "")).expanduser()
    if str(text_path) not in {"", "."} and text_path.is_dir():
        configured += 1
        yield from _chroma_records(
            text_path,
            os.environ.get("SAFEPLC_TEXT_COLLECTION", ""),
            "text_chroma",
            max_records_per_source,
        )
    figure_path = Path(os.environ.get("SAFEPLC_FIGURE_CHROMA_DIR", "")).expanduser()
    if str(figure_path) not in {"", "."} and figure_path.is_dir():
        configured += 1
        yield from _chroma_records(
            figure_path,
            os.environ.get("SAFEPLC_FIGURE_COLLECTION", ""),
            "figure_chroma",
            max_records_per_source,
        )
    for env_name in SOURCE_ENV:
        raw_path = os.environ.get(env_name, "")
        path = Path(raw_path).expanduser() if raw_path else Path()
        if raw_path and path.is_file():
            configured += 1
            yield from _jsonl_records(path, max_records_per_source)
    if not configured:
        raise AssetUnavailableError("No readable SAFEPLC Chroma or JSONL evidence assets are configured")


def build_evidence_seed_bank(
    output_path: Path = DEFAULT_SEED_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
    *,
    max_records_per_source: int = 0,
) -> Dict[str, Any]:
    records = configured_records(max_records_per_source=max_records_per_source)
    seeds, report = build_seed_bank_from_records(records)
    if not seeds:
        report["error"] = "No verified evidence seeds survived quality filtering"
        write_json(report_path, report)
        raise AssetUnavailableError(report["error"])
    write_jsonl(output_path, seeds)
    report["seed_bank_sha256"] = stable_hash(seeds)
    write_json(report_path, report)
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build a verified FULL-360 evidence seed bank from local assets.")
    parser.add_argument("--output", default=str(DEFAULT_SEED_PATH))
    parser.add_argument("--report", default=str(DEFAULT_REPORT_PATH))
    parser.add_argument("--max-records-per-source", type=int, default=0)
    args = parser.parse_args(argv)
    try:
        report = build_evidence_seed_bank(
            Path(args.output),
            Path(args.report),
            max_records_per_source=max(0, args.max_records_per_source),
        )
    except AssetUnavailableError as exc:
        blocked = {
            "schema": "safeplc.full_360.seed_bank_report.v1",
            "status": "BLOCKED",
            "seed_count": 0,
            "error": str(exc),
        }
        write_json(Path(args.report), blocked)
        print(json.dumps(blocked, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
