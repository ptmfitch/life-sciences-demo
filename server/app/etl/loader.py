"""ETL dry-run and load engine with idempotent ingestion."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.inspector import DEFAULT_MAPPING
from app.runs.events import broker
from app.sim.simulator import CSV_COLUMNS

REQUIRED = {"event_timestamp", "device_id", "assay_run_id", "well_id"}

FLOAT_FIELDS = {
    "temperature_c",
    "ph",
    "optical_density",
    "fluorescence_rfu",
    "dissolved_oxygen_pct",
    "reagent_concentration_mg_l",
    "activity_index",
}
INT_FIELDS = {"elapsed_seconds"}


def _parse_timestamp(raw: str) -> datetime:
    cleaned = raw.replace("Z", "+00:00")
    return datetime.fromisoformat(cleaned)


def _parse_value(field: str, raw: str) -> tuple[Any, str | None]:
    if raw is None or raw == "":
        if field in REQUIRED:
            return None, "missing_required"
        return None, "missing_optional" if field in FLOAT_FIELDS else None
    if field in INT_FIELDS:
        try:
            return int(float(raw)), None
        except ValueError:
            return None, "type_mismatch"
    if field in FLOAT_FIELDS:
        try:
            return float(raw), None
        except ValueError:
            return None, "type_mismatch"
    if field == "event_timestamp":
        try:
            return _parse_timestamp(raw), None
        except ValueError:
            return None, "invalid_timestamp"
    return raw, None


def _enabled_fields(mapping: dict[str, Any]) -> list[str]:
    fields = mapping.get("fields") or {}
    selected = mapping.get("selected") or list(CSV_COLUMNS)
    enabled = []
    for col in selected:
        cfg = fields.get(col, {"enabled": True, "destination": col})
        if cfg.get("enabled", True):
            enabled.append(col)
    return enabled


async def create_job(
    session: AsyncSession,
    *,
    job_type: str,
    file_ids: list[UUID],
    mapping: dict[str, Any],
) -> dict[str, Any]:
    job_id = uuid4()
    total = 0
    for fid in file_ids:
        result = await session.execute(
            text("SELECT row_count FROM source_files WHERE id = :id"), {"id": fid}
        )
        row = result.first()
        if row and row[0]:
            total += int(row[0])

    await session.execute(
        text(
            """
            INSERT INTO etl_jobs (
                id, job_type, status, file_ids, total_rows, result, started_at
            ) VALUES (
                :id, :jt, 'running', CAST(:files AS jsonb), :total, CAST(:result AS jsonb), NOW()
            )
            """
        ),
        {
            "id": job_id,
            "jt": job_type,
            "files": json.dumps([str(f) for f in file_ids]),
            "total": total,
            "result": json.dumps({"mapping": mapping}),
        },
    )
    await session.commit()
    return await get_job(session, job_id)


async def get_job(session: AsyncSession, job_id: UUID) -> dict[str, Any] | None:
    result = await session.execute(
        text("SELECT * FROM etl_jobs WHERE id = :id"), {"id": job_id}
    )
    row = result.mappings().first()
    if not row:
        return None
    job = dict(row)
    total = job["total_rows"] or 0
    processed = job["processed_rows"] or 0
    job["progress_pct"] = round(100 * processed / total, 1) if total else 0.0
    job["estimated_remaining_seconds"] = None
    if job.get("started_at") and processed > 0 and total > processed:
        elapsed = (datetime.now(timezone.utc) - job["started_at"].replace(tzinfo=timezone.utc)).total_seconds()
        rate = processed / max(elapsed, 0.001)
        job["estimated_remaining_seconds"] = round((total - processed) / rate, 1)
    return job


async def cancel_job(session: AsyncSession, job_id: UUID) -> dict[str, Any] | None:
    await session.execute(
        text(
            """
            UPDATE etl_jobs
            SET status = 'cancelled', completed_at = NOW()
            WHERE id = :id AND status = 'running'
            """
        ),
        {"id": job_id},
    )
    await session.commit()
    return await get_job(session, job_id)


async def run_etl(
    session: AsyncSession,
    job_id: UUID,
    *,
    dry_run: bool,
) -> dict[str, Any]:
    job = await get_job(session, job_id)
    if not job:
        raise KeyError("Job not found")

    mapping = (job.get("result") or {}).get("mapping") or DEFAULT_MAPPING
    enabled = _enabled_fields(mapping)
    file_ids = [UUID(x) for x in (job.get("file_ids") or [])]

    counters = {
        "processed_rows": 0,
        "inserted_rows": 0,
        "skipped_rows": 0,
        "rejected_rows": 0,
        "warning_rows": 0,
        "quarantined_rows": 0,
        "duplicate_files": 0,
        "files": [],
    }
    warnings: list[dict[str, Any]] = []
    rejects: list[dict[str, Any]] = []

    for fid in file_ids:
        # Check cancel
        current = await get_job(session, job_id)
        if current and current["status"] == "cancelled":
            break

        result = await session.execute(
            text("SELECT * FROM source_files WHERE id = :id"), {"id": fid}
        )
        sf = result.mappings().first()
        if not sf:
            continue

        file_summary: dict[str, Any] = {
            "id": str(fid),
            "filename": sf["filename"],
            "status": sf["ingestion_status"],
        }

        if not dry_run and sf["ingestion_status"] == "ingested":
            counters["duplicate_files"] += 1
            counters["skipped_rows"] += int(sf["row_count"] or 0)
            file_summary["skipped"] = True
            file_summary["reason"] = "already_ingested"
            counters["files"].append(file_summary)
            continue

        path = Path(sf["filepath"])
        if not path.exists():
            file_summary["error"] = "file_missing"
            counters["files"].append(file_summary)
            continue

        await session.execute(
            text(
                """
                UPDATE etl_jobs
                SET current_file = :fn, current_phase = :phase
                WHERE id = :id
                """
            ),
            {"id": job_id, "fn": sf["filename"], "phase": "dry_run" if dry_run else "load"},
        )
        await session.commit()

        seen_keys: set[tuple] = set()
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row_number, raw in enumerate(reader, start=1):
                counters["processed_rows"] += 1
                parsed: dict[str, Any] = {}
                row_warnings: list[str] = []
                rejected = False

                for field in enabled:
                    dest = (
                        mapping.get("fields", {}).get(field, {}).get("destination") or field
                    )
                    value, issue = _parse_value(field, raw.get(field, ""))
                    if issue == "missing_required" or issue == "type_mismatch" or issue == "invalid_timestamp":
                        rejected = True
                        rejects.append(
                            {
                                "file": sf["filename"],
                                "row": row_number,
                                "field": field,
                                "issue": issue,
                                "value": raw.get(field),
                            }
                        )
                    elif issue == "missing_optional":
                        row_warnings.append(f"{field}:missing")
                    parsed[dest] = value

                # Range sanity (warnings only)
                temp = parsed.get("temperature_c")
                if temp is not None and (temp < 20 or temp > 45):
                    row_warnings.append("temperature_excursion")
                if raw.get("quality_flag") in ("review", "missing_check"):
                    row_warnings.append(f"quality:{raw.get('quality_flag')}")

                key = (
                    parsed.get("device_id"),
                    parsed.get("assay_run_id"),
                    parsed.get("event_timestamp"),
                    parsed.get("well_id"),
                )
                if key in seen_keys:
                    row_warnings.append("duplicate_row")
                else:
                    seen_keys.add(key)

                if rejected:
                    counters["rejected_rows"] += 1
                    counters["quarantined_rows"] += 1
                    continue

                if row_warnings:
                    counters["warning_rows"] += 1
                    warnings.append(
                        {
                            "file": sf["filename"],
                            "row": row_number,
                            "warnings": row_warnings,
                        }
                    )

                if not dry_run:
                    # Preserve raw
                    await session.execute(
                        text(
                            """
                            INSERT INTO raw_readings (source_file_id, row_number, payload)
                            VALUES (:sf, :rn, CAST(:payload AS jsonb))
                            ON CONFLICT (source_file_id, row_number) DO NOTHING
                            """
                        ),
                        {
                            "sf": fid,
                            "rn": row_number,
                            "payload": json.dumps(raw),
                        },
                    )
                    # Typed insert
                    await session.execute(
                        text(
                            """
                            INSERT INTO telemetry_readings (
                                source_file_id, event_timestamp, test_name, device_name,
                                device_id, rack_id, well_id, assay_run_id, sample_id,
                                compound_code, elapsed_seconds, temperature_c, ph,
                                optical_density, fluorescence_rfu, dissolved_oxygen_pct,
                                reagent_concentration_mg_l, activity_index, status, quality_flag
                            ) VALUES (
                                :sf,
                                :event_timestamp,
                                :test_name, :device_name, :device_id, :rack_id, :well_id,
                                :assay_run_id, :sample_id, :compound_code, :elapsed_seconds,
                                :temperature_c, :ph, :optical_density, :fluorescence_rfu,
                                :dissolved_oxygen_pct, :reagent_concentration_mg_l,
                                :activity_index, :status, :quality_flag
                            )
                            ON CONFLICT (device_id, assay_run_id, event_timestamp, well_id)
                            DO NOTHING
                            """
                        ),
                        {
                            "sf": fid,
                            "event_timestamp": parsed.get("event_timestamp"),
                            "test_name": parsed.get("test_name") or "",
                            "device_name": parsed.get("device_name") or "AstraLume BioTest Station",
                            "device_id": parsed.get("device_id"),
                            "rack_id": parsed.get("rack_id") or "",
                            "well_id": parsed.get("well_id"),
                            "assay_run_id": parsed.get("assay_run_id"),
                            "sample_id": parsed.get("sample_id") or "",
                            "compound_code": parsed.get("compound_code") or "",
                            "elapsed_seconds": parsed.get("elapsed_seconds") or 0,
                            "temperature_c": parsed.get("temperature_c"),
                            "ph": parsed.get("ph"),
                            "optical_density": parsed.get("optical_density"),
                            "fluorescence_rfu": parsed.get("fluorescence_rfu"),
                            "dissolved_oxygen_pct": parsed.get("dissolved_oxygen_pct"),
                            "reagent_concentration_mg_l": parsed.get("reagent_concentration_mg_l"),
                            "activity_index": parsed.get("activity_index"),
                            "status": parsed.get("status"),
                            "quality_flag": parsed.get("quality_flag"),
                        },
                    )
                    counters["inserted_rows"] += 1
                else:
                    counters["inserted_rows"] += 1  # would-insert

                if counters["processed_rows"] % 50 == 0:
                    await session.execute(
                        text(
                            """
                            UPDATE etl_jobs SET
                                processed_rows = :p, inserted_rows = :i, skipped_rows = :s,
                                rejected_rows = :r, warning_rows = :w, quarantined_rows = :q
                            WHERE id = :id
                            """
                        ),
                        {
                            "id": job_id,
                            "p": counters["processed_rows"],
                            "i": counters["inserted_rows"],
                            "s": counters["skipped_rows"],
                            "r": counters["rejected_rows"],
                            "w": counters["warning_rows"],
                            "q": counters["quarantined_rows"],
                        },
                    )
                    await session.commit()
                    job_snap = await get_job(session, job_id)
                    await broker.publish("etl_progress", job_snap)

        if not dry_run:
            await session.execute(
                text(
                    """
                    UPDATE source_files
                    SET ingestion_status = 'ingested', ingested_at = NOW()
                    WHERE id = :id
                    """
                ),
                {"id": fid},
            )
        file_summary["rows"] = sf["row_count"]
        counters["files"].append(file_summary)

    result_payload = {
        "mapping": mapping,
        "dry_run": dry_run,
        "no_database_changes": dry_run,
        "counters": counters,
        "warnings": warnings[:100],
        "rejects": rejects[:100],
        "warning_total": len(warnings),
        "reject_total": len(rejects),
    }

    await session.execute(
        text(
            """
            UPDATE etl_jobs SET
                status = 'complete',
                processed_rows = :p, inserted_rows = :i, skipped_rows = :s,
                rejected_rows = :r, warning_rows = :w, quarantined_rows = :q,
                current_phase = 'complete', completed_at = NOW(),
                result = CAST(:result AS jsonb)
            WHERE id = :id
            """
        ),
        {
            "id": job_id,
            "p": counters["processed_rows"],
            "i": counters["inserted_rows"],
            "s": counters["skipped_rows"],
            "r": counters["rejected_rows"],
            "w": counters["warning_rows"],
            "q": counters["quarantined_rows"],
            "result": json.dumps(result_payload),
        },
    )
    await session.commit()
    job = await get_job(session, job_id)
    await broker.publish("etl_progress", job)
    return job