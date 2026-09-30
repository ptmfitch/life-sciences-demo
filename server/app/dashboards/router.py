"""Dashboard aggregate endpoints."""

from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit_trail.records import acceptance_recalculation_record
from app.audit_trail.store import insert_audit_event, list_audit_events
from app.db import get_session
from app.validated.acceptance import (
    REFERENCE_SPECIMENS,
    AcceptanceBatch,
    SpecimenInput,
    disposition_to_dict,
    recalculate_acceptance,
    spec_payload,
)

router = APIRouter(prefix="/dash", tags=["dashboards"])

ALLOWED_METRICS = {
    "temperature_c",
    "ph",
    "optical_density",
    "fluorescence_rfu",
    "dissolved_oxygen_pct",
    "reagent_concentration_mg_l",
    "activity_index",
}


@router.get("/timeseries")
async def timeseries(
    fields: str = Query("temperature_c,optical_density"),
    device_id: str | None = None,
    assay_run_id: str | None = None,
    limit: int = Query(2000, ge=10, le=20000),
    session: AsyncSession = Depends(get_session),
):
    selected = [f.strip() for f in fields.split(",") if f.strip() in ALLOWED_METRICS]
    if not selected:
        selected = ["temperature_c"]
    cols = ", ".join(selected)
    clauses = ["1=1"]
    params: dict = {"limit": limit}
    if device_id:
        clauses.append("device_id = :device_id")
        params["device_id"] = device_id
    if assay_run_id:
        clauses.append("assay_run_id = :assay_run_id")
        params["assay_run_id"] = assay_run_id
    where = " AND ".join(clauses)
    sql = f"""
        SELECT event_timestamp, elapsed_seconds, device_id, assay_run_id, test_name, {cols}
        FROM telemetry_readings
        WHERE {where}
        ORDER BY event_timestamp ASC
        LIMIT :limit
    """
    result = await session.execute(text(sql), params)
    rows = [dict(r) for r in result.mappings().all()]
    return {
        "fields": selected,
        "filters": {"device_id": device_id, "assay_run_id": assay_run_id},
        "points": rows,
        "disclaimer": "Synthetic illustrative data — demo thresholds only.",
    }


@router.get("/compare")
async def compare(
    field: str = Query("activity_index"),
    session: AsyncSession = Depends(get_session),
):
    if field not in ALLOWED_METRICS:
        field = "activity_index"
    sql = f"""
        SELECT device_id, rack_id, assay_run_id, test_name,
               AVG({field}) AS avg_value,
               MIN({field}) AS min_value,
               MAX({field}) AS max_value,
               COUNT(*) AS n
        FROM telemetry_readings
        GROUP BY device_id, rack_id, assay_run_id, test_name
        ORDER BY avg_value DESC
    """
    result = await session.execute(text(sql))
    return {
        "field": field,
        "rows": [dict(r) for r in result.mappings().all()],
        "disclaimer": "Synthetic illustrative comparisons.",
    }


@router.get("/status-distribution")
async def status_distribution(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        text(
            """
            SELECT device_id, status, COUNT(*) AS n
            FROM telemetry_readings
            GROUP BY device_id, status
            ORDER BY device_id, status
            """
        )
    )
    return {
        "rows": [dict(r) for r in result.mappings().all()],
        "note": "Status values are synthetic operational labels, not clinical results.",
    }


@router.get("/quality")
async def quality(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        text(
            """
            SELECT
              COUNT(*) AS total_rows,
              COUNT(*) FILTER (WHERE quality_flag = 'pass') AS pass_rows,
              COUNT(*) FILTER (WHERE quality_flag = 'review') AS review_rows,
              COUNT(*) FILTER (WHERE quality_flag = 'missing_check') AS missing_check_rows,
              COUNT(*) FILTER (WHERE dissolved_oxygen_pct IS NULL) AS missing_do,
              COUNT(DISTINCT device_id) AS devices,
              COUNT(DISTINCT assay_run_id) AS assay_runs
            FROM telemetry_readings
            """
        )
    )
    summary = dict(result.mappings().one())
    return {
        "summary": summary,
        "disclaimer": "Data-quality flags are synthetic demo markers.",
    }


@router.get("/well-heatmap")
async def well_heatmap(
    assay_run_id: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    params: dict = {}
    clause = ""
    if assay_run_id:
        clause = "WHERE assay_run_id = :assay_run_id"
        params["assay_run_id"] = assay_run_id
    sql = f"""
        SELECT well_id, AVG(activity_index) AS avg_activity,
               AVG(optical_density) AS avg_od,
               COUNT(*) AS n
        FROM telemetry_readings
        {clause}
        GROUP BY well_id
        ORDER BY well_id
    """
    result = await session.execute(text(sql), params)
    return {
        "assay_run_id": assay_run_id,
        "cells": [dict(r) for r in result.mappings().all()],
        "disclaimer": "Synthetic well activity — illustrative visualisation only.",
    }


@router.get("/filters")
async def filters(session: AsyncSession = Depends(get_session)):
    devices = await session.execute(
        text("SELECT DISTINCT device_id FROM telemetry_readings ORDER BY device_id")
    )
    assays = await session.execute(
        text("SELECT DISTINCT assay_run_id FROM telemetry_readings ORDER BY assay_run_id")
    )
    tests = await session.execute(
        text("SELECT DISTINCT test_name FROM telemetry_readings ORDER BY test_name")
    )
    return {
        "device_ids": [r[0] for r in devices.fetchall()],
        "assay_run_ids": [r[0] for r in assays.fetchall()],
        "test_names": [r[0] for r in tests.fetchall()],
        "metrics": sorted(ALLOWED_METRICS),
    }


async def _loaded_specimens(session: AsyncSession) -> list[SpecimenInput]:
    result = await session.execute(
        text(
            """
            SELECT assay_run_id, test_name,
                   AVG(activity_index) AS avg_activity,
                   AVG(temperature_c) AS avg_temperature
            FROM telemetry_readings
            WHERE activity_index IS NOT NULL
              AND temperature_c IS NOT NULL
            GROUP BY assay_run_id, test_name
            ORDER BY test_name, assay_run_id
            LIMIT 12
            """
        )
    )
    specimens: list[SpecimenInput] = []
    for row in result.mappings().all():
        label = f"{row['test_name']} ({row['assay_run_id']})"
        specimens.append(
            SpecimenInput(
                label=label,
                activity_index=Decimal(str(row["avg_activity"])),
                temperature_c=Decimal(str(row["avg_temperature"])),
            )
        )
    return specimens


def _acceptance_body(batch: AcceptanceBatch, loaded_count: int) -> dict:
    body = spec_payload()
    body["reference_specimens"] = [disposition_to_dict(item) for item in batch.reference]
    body["loaded_runs"] = [disposition_to_dict(item) for item in batch.loaded]
    body["loaded_run_count"] = loaded_count
    return body


@router.get("/acceptance")
async def acceptance(session: AsyncSession = Depends(get_session)):
    loaded = await _loaded_specimens(session)
    batch = recalculate_acceptance(REFERENCE_SPECIMENS, loaded)
    return _acceptance_body(batch, len(loaded))


@router.post("/acceptance/recalculate")
async def recalculate(session: AsyncSession = Depends(get_session)):
    loaded = await _loaded_specimens(session)
    batch = recalculate_acceptance(REFERENCE_SPECIMENS, loaded)
    outcomes = (*batch.reference, *batch.loaded)
    pass_count = sum(1 for item in outcomes if item.overall == "PASS")
    fail_count = sum(1 for item in outcomes if item.overall == "FAIL")
    record = acceptance_recalculation_record(
        specimen_count=len(outcomes),
        pass_count=pass_count,
        fail_count=fail_count,
        loaded_run_count=len(batch.loaded),
    )
    await insert_audit_event(session, record)
    await session.commit()
    body = _acceptance_body(batch, len(loaded))
    body["audit_events"] = await list_audit_events(session, limit=8)
    return body