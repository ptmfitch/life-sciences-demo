"""CSV schema inspector."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any

from app.sim.simulator import CSV_COLUMNS

IDENTIFIER_FIELDS = {
    "test_name",
    "device_name",
    "device_id",
    "rack_id",
    "well_id",
    "assay_run_id",
    "sample_id",
    "compound_code",
}
TIMESTAMP_FIELDS = {"event_timestamp"}
TELEMETRY_FIELDS = {
    "elapsed_seconds",
    "temperature_c",
    "ph",
    "optical_density",
    "fluorescence_rfu",
    "dissolved_oxygen_pct",
    "reagent_concentration_mg_l",
}
DERIVED_FIELDS = {"activity_index"}
QUALITY_FIELDS = {"status", "quality_flag"}


def categorize(column: str) -> str:
    if column in IDENTIFIER_FIELDS:
        return "identifier"
    if column in TIMESTAMP_FIELDS:
        return "timestamp"
    if column in TELEMETRY_FIELDS:
        return "telemetry"
    if column in DERIVED_FIELDS:
        return "derived"
    if column in QUALITY_FIELDS:
        return "quality"
    return "other"


def infer_type(values: list[str]) -> str:
    non_empty = [v for v in values if v not in ("", None)]
    if not non_empty:
        return "empty"
    if all(_is_int(v) for v in non_empty):
        return "integer"
    if all(_is_float(v) for v in non_empty):
        return "float"
    if all(_looks_ts(v) for v in non_empty):
        return "timestamp"
    return "string"


def _is_int(v: str) -> bool:
    try:
        int(v)
        return True
    except ValueError:
        return False


def _is_float(v: str) -> bool:
    try:
        float(v)
        return True
    except ValueError:
        return False


def _looks_ts(v: str) -> bool:
    return "T" in v or "-" in v[:10]


def inspect_file(path: Path, preview_rows: int = 8) -> dict[str, Any]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        columns = reader.fieldnames or []
        rows = []
        for i, row in enumerate(reader):
            rows.append(row)
            if i >= 499:
                break

    col_stats = []
    for col in columns:
        values = [r.get(col, "") or "" for r in rows]
        nulls = sum(1 for v in values if v == "")
        examples = [v for v in values if v][:3]
        numeric = [float(v) for v in values if v and _is_float(v)]
        stats: dict[str, Any] = {
            "name": col,
            "category": categorize(col),
            "inferred_type": infer_type(values),
            "null_count": nulls,
            "null_pct": round(100 * nulls / max(len(values), 1), 1),
            "examples": examples,
            "known_schema": col in CSV_COLUMNS,
        }
        if numeric:
            stats["min"] = round(min(numeric), 4)
            stats["max"] = round(max(numeric), 4)
            stats["mean"] = round(sum(numeric) / len(numeric), 4)
        col_stats.append(stats)

    # Duplicate timestamp candidates in preview
    ts_counts = Counter(r.get("event_timestamp") for r in rows if r.get("event_timestamp"))
    dup_ts = sum(1 for _, c in ts_counts.items() if c > 1)

    return {
        "filename": path.name,
        "filepath": str(path),
        "columns": col_stats,
        "preview": rows[:preview_rows],
        "sampled_rows": len(rows),
        "duplicate_timestamp_candidates": dup_ts,
        "field_groups": {
            "identifier": [c for c in columns if categorize(c) == "identifier"],
            "timestamp": [c for c in columns if categorize(c) == "timestamp"],
            "telemetry": [c for c in columns if categorize(c) == "telemetry"],
            "derived": [c for c in columns if categorize(c) == "derived"],
            "quality": [c for c in columns if categorize(c) == "quality"],
            "other": [c for c in columns if categorize(c) == "other"],
        },
    }


DEFAULT_MAPPING = {
    "selected": list(CSV_COLUMNS),
    "fields": {col: {"destination": col, "enabled": True} for col in CSV_COLUMNS},
    "required": ["event_timestamp", "device_id", "assay_run_id", "well_id"],
}