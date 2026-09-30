"""Read API for the append-only demo audit trail."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit_trail.store import list_audit_events
from app.db import get_session

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
async def list_events(
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    return await list_audit_events(session, limit=limit)
