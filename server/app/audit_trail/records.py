"""Pure audit records. Persistence lives in ``store``; this module never updates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID, uuid4


@dataclass(frozen=True)
class AuditRecord:
    event_id: UUID
    recorded_at: datetime
    actor: str
    action: str
    reason: str
    subject_type: str
    subject_id: str
    details: Mapping[str, Any]


def make_record(
    *,
    actor: str,
    action: str,
    reason: str,
    subject_type: str,
    subject_id: str,
    details: Mapping[str, Any] | None = None,
    recorded_at: datetime | None = None,
    event_id: UUID | None = None,
) -> AuditRecord:
    when = recorded_at or datetime.now(timezone.utc)
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return AuditRecord(
        event_id=event_id or uuid4(),
        recorded_at=when,
        actor=actor,
        action=action,
        reason=reason,
        subject_type=subject_type,
        subject_id=subject_id,
        details=MappingProxyType(dict(details or {})),
    )


def etl_load_record(
    *,
    job_id: str,
    inserted_rows: int,
    skipped_rows: int,
    rejected_rows: int,
    file_count: int,
) -> AuditRecord:
    return make_record(
        actor="console.etl",
        action="etl_load_committed",
        reason="Commit mapped CSV rows into telemetry_readings",
        subject_type="etl_job",
        subject_id=job_id,
        details={
            "inserted_rows": inserted_rows,
            "skipped_rows": skipped_rows,
            "rejected_rows": rejected_rows,
            "file_count": file_count,
        },
    )


def acceptance_recalculation_record(
    *,
    specimen_count: int,
    pass_count: int,
    fail_count: int,
    loaded_run_count: int,
) -> AuditRecord:
    return make_record(
        actor="console.dashboard",
        action="acceptance_recalculated",
        reason="Recalculate specimen acceptance for the dashboard panel",
        subject_type="acceptance_panel",
        subject_id="reference-standards",
        details={
            "specimen_count": specimen_count,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "loaded_run_count": loaded_run_count,
        },
    )


class AppendOnlyLog:
    """In-memory log that only appends. Used to pin the write contract in tests."""

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    def append(self, record: AuditRecord) -> AuditRecord:
        if not isinstance(record, AuditRecord):
            raise TypeError("record must be an AuditRecord")
        self._records.append(record)
        return record

    def records(self) -> tuple[AuditRecord, ...]:
        return tuple(self._records)
