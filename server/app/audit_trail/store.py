"""Postgres insert and list for audit events. No update or delete helpers."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit_trail.records import AuditRecord


async def insert_audit_event(session: AsyncSession, record: AuditRecord) -> None:
    await session.execute(
        text(
            """
            INSERT INTO audit_events (
                id, recorded_at, actor, action, reason,
                subject_type, subject_id, details
            ) VALUES (
                :id, :recorded_at, :actor, :action, :reason,
                :subject_type, :subject_id, CAST(:details AS jsonb)
            )
            """
        ),
        {
            "id": record.event_id,
            "recorded_at": record.recorded_at,
            "actor": record.actor,
            "action": record.action,
            "reason": record.reason,
            "subject_type": record.subject_type,
            "subject_id": record.subject_id,
            "details": json.dumps(dict(record.details)),
        },
    )


async def list_audit_events(session: AsyncSession, *, limit: int = 50) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            """
            SELECT id, recorded_at, actor, action, reason,
                   subject_type, subject_id, details
            FROM audit_events
            ORDER BY recorded_at DESC, id DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    )
    rows: list[dict[str, Any]] = []
    for row in result.mappings().all():
        item = dict(row)
        item["id"] = str(item["id"])
        rows.append(item)
    return rows
