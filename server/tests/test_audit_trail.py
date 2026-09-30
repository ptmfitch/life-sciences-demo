"""Append-only audit records: who, what, when, why."""

from dataclasses import FrozenInstanceError

from app.audit_trail.records import (
    AppendOnlyLog,
    acceptance_recalculation_record,
    etl_load_record,
    make_record,
)


def test_etl_load_record_names_who_what_when_why():
    record = etl_load_record(
        job_id="job-1",
        inserted_rows=60,
        skipped_rows=0,
        rejected_rows=1,
        file_count=1,
    )
    assert record.actor == "console.etl"
    assert record.action == "etl_load_committed"
    assert record.reason
    assert record.recorded_at.tzinfo is not None
    assert record.subject_type == "etl_job"
    assert record.subject_id == "job-1"
    assert record.details["inserted_rows"] == 60
    assert record.details["file_count"] == 1


def test_recalculation_record_names_who_what_when_why():
    record = acceptance_recalculation_record(
        specimen_count=5,
        pass_count=2,
        fail_count=3,
        loaded_run_count=0,
    )
    assert record.actor == "console.dashboard"
    assert record.action == "acceptance_recalculated"
    assert "dashboard" in record.reason
    assert record.recorded_at.tzinfo is not None
    assert record.details["pass_count"] == 2
    assert record.details["fail_count"] == 3


def test_record_details_are_copied():
    payload = {"inserted_rows": 1}
    record = make_record(
        actor="console.etl",
        action="etl_load_committed",
        reason="Commit mapped CSV rows into telemetry_readings",
        subject_type="etl_job",
        subject_id="job-2",
        details=payload,
    )
    payload["inserted_rows"] = 99
    assert record.details["inserted_rows"] == 1


def test_append_does_not_rewrite_earlier_records():
    log = AppendOnlyLog()
    first = log.append(
        etl_load_record(
            job_id="job-a",
            inserted_rows=10,
            skipped_rows=0,
            rejected_rows=0,
            file_count=1,
        )
    )
    log.append(
        etl_load_record(
            job_id="job-b",
            inserted_rows=4,
            skipped_rows=2,
            rejected_rows=0,
            file_count=1,
        )
    )
    stored = log.records()
    assert stored[0] is first
    assert stored[0].subject_id == "job-a"
    assert stored[0].details["inserted_rows"] == 10
    assert len(stored) == 2
    assert isinstance(stored, tuple)


def test_record_fields_are_frozen():
    record = acceptance_recalculation_record(
        specimen_count=1,
        pass_count=1,
        fail_count=0,
        loaded_run_count=0,
    )
    try:
        record.actor = "someone-else"  # type: ignore[misc]
    except FrozenInstanceError:
        return
    raise AssertionError("audit record accepted a field write")


def test_log_rejects_non_records():
    log = AppendOnlyLog()
    try:
        log.append("not-a-record")  # type: ignore[arg-type]
    except TypeError:
        return
    raise AssertionError("log accepted a non-record")
