"""Persisted field mapping helpers."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.inspector import DEFAULT_MAPPING


async def list_mappings(session: AsyncSession) -> list[dict[str, Any]]:
    result = await session.execute(
        text("SELECT * FROM field_mappings ORDER BY updated_at DESC")
    )
    return [dict(r) for r in result.mappings().all()]


async def save_mapping(
    session: AsyncSession, name: str, mapping: dict[str, Any]
) -> dict[str, Any]:
    existing = await session.execute(
        text("SELECT id FROM field_mappings WHERE name = :n"), {"n": name}
    )
    row = existing.first()
    if row:
        mid = row[0]
        await session.execute(
            text(
                """
                UPDATE field_mappings
                SET mapping = CAST(:m AS jsonb), updated_at = NOW()
                WHERE id = :id
                """
            ),
            {"id": mid, "m": json.dumps(mapping)},
        )
    else:
        mid = uuid4()
        await session.execute(
            text(
                """
                INSERT INTO field_mappings (id, name, mapping)
                VALUES (:id, :n, CAST(:m AS jsonb))
                """
            ),
            {"id": mid, "n": name, "m": json.dumps(mapping)},
        )
    await session.commit()
    result = await session.execute(
        text("SELECT * FROM field_mappings WHERE id = :id"), {"id": mid}
    )
    return dict(result.mappings().one())


async def get_mapping(session: AsyncSession, mapping_id: UUID) -> dict[str, Any] | None:
    result = await session.execute(
        text("SELECT * FROM field_mappings WHERE id = :id"), {"id": mapping_id}
    )
    row = result.mappings().first()
    return dict(row) if row else None


def default_mapping() -> dict[str, Any]:
    return dict(DEFAULT_MAPPING)