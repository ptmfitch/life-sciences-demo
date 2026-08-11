from uuid import UUID

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.runs.events import broker, sse_format
from app.runs.manager import RunManager
from app.schemas import BulkRequest, CreateRunRequest, RunOut

router = APIRouter(tags=["runs"])


def get_manager(request: Request) -> RunManager:
    return request.app.state.manager


@router.post("/runs", response_model=list[RunOut])
async def create_runs(
    body: CreateRunRequest,
    session: AsyncSession = Depends(get_session),
    manager: RunManager = Depends(get_manager),
):
    runs = await manager.create_runs(
        session,
        test_name=body.test_name,
        quantity=body.quantity,
        device_id=body.device_id,
        rack_id=body.rack_id,
        assay_run_id=body.assay_run_id,
        compound_code=body.compound_code,
        well_count=body.well_count,
        seed=body.seed,
    )
    return runs


@router.get("/runs", response_model=list[RunOut])
async def list_runs(
    session: AsyncSession = Depends(get_session),
    manager: RunManager = Depends(get_manager),
):
    return await manager.list_runs(session)


@router.get("/runs/{run_id}", response_model=RunOut)
async def get_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
    manager: RunManager = Depends(get_manager),
):
    run = await manager.get_run(session, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return run


@router.post("/runs/{run_id}/start", response_model=RunOut)
async def start_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
    manager: RunManager = Depends(get_manager),
):
    try:
        return await manager.start(session, run_id)
    except KeyError:
        raise HTTPException(404, "Run not found") from None
    except RuntimeError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/runs/{run_id}/pause", response_model=RunOut)
async def pause_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
    manager: RunManager = Depends(get_manager),
):
    return await manager.pause(session, run_id)


@router.post("/runs/{run_id}/resume", response_model=RunOut)
async def resume_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
    manager: RunManager = Depends(get_manager),
):
    return await manager.resume(session, run_id)


@router.post("/runs/{run_id}/stop", response_model=RunOut)
async def stop_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
    manager: RunManager = Depends(get_manager),
):
    return await manager.stop(session, run_id)


@router.post("/runs/{run_id}/restart", response_model=RunOut)
async def restart_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
    manager: RunManager = Depends(get_manager),
):
    try:
        return await manager.restart(session, run_id)
    except RuntimeError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.delete("/runs/{run_id}")
async def clear_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
    manager: RunManager = Depends(get_manager),
):
    await manager.clear(session, run_id)
    return {"ok": True}


@router.post("/runs/bulk", response_model=list[RunOut])
async def bulk_action(
    body: BulkRequest,
    session: AsyncSession = Depends(get_session),
    manager: RunManager = Depends(get_manager),
):
    return await manager.bulk(session, body.action)


@router.get("/stream")
async def stream(
    request: Request,
    session: AsyncSession = Depends(get_session),
    manager: RunManager = Depends(get_manager),
):
    queue = broker.subscribe()

    async def event_generator():
        try:
            runs = await manager.list_runs(session)
            snap = broker.snapshot(runs)
            yield sse_format("snapshot", snap)
            while True:
                if await request.is_disconnected():
                    break
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=5.0)
                    yield sse_format(message["type"], message["data"])
                except TimeoutError:
                    yield sse_format("heartbeat", {"ok": True})
        finally:
            broker.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )