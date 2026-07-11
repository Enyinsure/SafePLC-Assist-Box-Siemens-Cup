#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .embedding_adapter import collection_embedding_dimension


class CollectionSelectionError(RuntimeError):
    pass


class AmbiguousCollectionError(CollectionSelectionError):
    pass


class EmptyCollectionError(CollectionSelectionError):
    pass


def discover_collections(client: Any, path: str = "") -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    try:
        listed = client.list_collections()
    except Exception as exc:
        raise CollectionSelectionError(f"Unable to list Chroma collections under {path}: {exc}") from exc
    for listed_item in listed:
        name = getattr(listed_item, "name", None) or str(listed_item)
        collection = client.get_collection(name) if isinstance(listed_item, str) else listed_item
        row: Dict[str, Any] = {
            "name": name,
            "count": None,
            "metadata_fields": [],
            "embedding_dimension": None,
            "collection_metadata": dict(getattr(collection, "metadata", None) or {}),
            "path": path,
            "error": "",
        }
        errors: List[str] = []
        try:
            row["count"] = int(collection.count())
        except Exception as exc:
            errors.append(f"count failed: {exc}")
        try:
            peek = collection.peek(5)
            fields = {
                str(key)
                for meta in (peek.get("metadatas", []) or [])
                if isinstance(meta, dict)
                for key in meta
            }
            row["metadata_fields"] = sorted(fields)
        except Exception as exc:
            errors.append(f"peek failed: {exc}")
        try:
            row["embedding_dimension"] = collection_embedding_dimension(collection)
        except Exception as exc:
            errors.append(f"embedding inspection failed: {exc}")
        row["error"] = "; ".join(errors)
        rows.append(row)
    return rows


def select_collection(
    client: Any,
    rows: List[Dict[str, Any]],
    explicit_name: str = "",
    kind: str = "text",
) -> Tuple[str, Any, Dict[str, Any]]:
    if not rows:
        raise EmptyCollectionError(f"No {kind} Chroma collections were found.")
    by_name = {str(row["name"]): row for row in rows}
    if explicit_name:
        if explicit_name not in by_name:
            raise CollectionSelectionError(
                f"Configured {kind} collection {explicit_name!r} was not found. Available: {_describe(rows)}"
            )
        selected = by_name[explicit_name]
        if selected.get("count") is None:
            raise CollectionSelectionError(
                f"Configured {kind} collection {explicit_name!r} could not be inspected: {selected.get('error')}"
            )
        if int(selected.get("count") or 0) <= 0:
            raise EmptyCollectionError(f"Configured {kind} collection {explicit_name!r} is empty.")
    else:
        non_empty = [row for row in rows if isinstance(row.get("count"), int) and int(row["count"]) > 0]
        if not non_empty:
            raise EmptyCollectionError(f"All {kind} Chroma collections are empty or unreadable: {_describe(rows)}")
        if len(non_empty) > 1:
            raise AmbiguousCollectionError(
                f"Multiple non-empty {kind} Chroma collections require explicit configuration: {_describe(non_empty)}"
            )
        selected = non_empty[0]
    name = str(selected["name"])
    collection = client.get_collection(name)
    return name, collection, selected


def _describe(rows: List[Dict[str, Any]]) -> str:
    return ", ".join(
        f"{row.get('name')} (count={row.get('count')}, metadata_fields={row.get('metadata_fields')}, error={row.get('error')!r})"
        for row in rows
    )
