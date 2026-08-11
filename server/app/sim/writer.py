"""CSV writer for one-minute telemetry files."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.sim.simulator import CSV_COLUMNS, slugify


def safe_timestamp(dt: datetime | None = None) -> str:
    dt = dt or datetime.now(timezone.utc)
    # Filesystem-safe ISO-8601
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_filename(test_name: str, device_id: str, when: datetime | None = None) -> str:
    slug = slugify(test_name)
    return f"AstraLume-BioTest-Station-{slug}-{device_id}-{safe_timestamp(when)}.csv"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.parent.exists() or not path.parent.is_dir():
        raise OSError(f"Output directory unavailable: {path.parent}")

    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out = {k: row.get(k) for k in CSV_COLUMNS}
            # Empty string for None so CSV stays consistent
            for k, v in out.items():
                if v is None:
                    out[k] = ""
            writer.writerow(out)
    return path


def maybe_duplicate_row(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Insert a duplicate-looking row (same timestamp) if any row flags it."""
    result: list[dict[str, Any]] = []
    planted = False
    for row in rows:
        clean = {k: v for k, v in row.items() if not k.startswith("_")}
        result.append(clean)
        if row.get("_duplicate_candidate") and not planted:
            dup = dict(clean)
            dup["quality_flag"] = "review"
            result.append(dup)
            planted = True
    return result