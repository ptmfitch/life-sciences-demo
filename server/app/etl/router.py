import asyncio
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal, get_session
from app.etl import loader
from app.etl.inspector import inspect_file
from app.etl.mappings import default_mapping, get_mapping, list_mappings, save_mapping
from app.etl.scanner import scan_directory
from app.schemas import EtlJobOut, EtlJobRequest, FieldMappingCreate, FieldMappingOut

router = APIRouter(prefix="/etl", tags=["etl"])


@router.post("/scan")
async def scan(session: AsyncSession = Depends(get_session)):
    return await scan_directory(session)


@router.get("/files")
async def files(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        text("SELECT * FROM source_files ORDER BY discovered_at DESC")
    )
    return [dict(r) for r in result.mappings().all()]


@router.get("/files/{file_id}/inspect")
async def inspect(file_id: UUID, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        text("SELECT * FROM source_files WHERE id = :id"), {"id": file_id}
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(404, "File not found")
    path = Path(row["filepath"])
    if not path.exists():
        raise HTTPException(404, "File missing on disk")
    return inspect_file(path)


@router.get("/mappings", response_model=list[FieldMappingOut])
async def get_mappings(session: AsyncSession = Depends(get_session)):
    return await list_mappings(session)


@router.get("/mappings/default")
async def get_default_mapping():
    return default_mapping()


@router.post("/mappings", response_model=FieldMappingOut)
async def create_mapping(
    body: FieldMappingCreate, session: AsyncSession = Depends(get_session)
):
    return await save_mapping(session, body.name, body.mapping)


@router.post("/dry-run", response_model=EtlJobOut)
async def dry_run(body: EtlJobRequest, session: AsyncSession = Depends(get_session)):
    mapping = body.mapping
    if body.mapping_id:
        saved = await get_mapping(session, body.mapping_id)
        if not saved:
            raise HTTPException(404, "Mapping not found")
        mapping = saved["mapping"]
    if not mapping:
        mapping = default_mapping()

    job = await loader.create_job(
        session, job_type="dry_run", file_ids=body.file_ids, mapping=mapping
    )
    # Run inline for simplicity (small demo volumes)
    job = await loader.run_etl(session, job["id"], dry_run=True)
    return job


@router.post("/load", response_model=EtlJobOut)
async def load(body: EtlJobRequest, session: AsyncSession = Depends(get_session)):
    mapping = body.mapping
    if body.mapping_id:
        saved = await get_mapping(session, body.mapping_id)
        if not saved:
            raise HTTPException(404, "Mapping not found")
        mapping = saved["mapping"]
    if not mapping:
        mapping = default_mapping()

    job = await loader.create_job(
        session, job_type="load", file_ids=body.file_ids, mapping=mapping
    )
    job_id = job["id"]

    async def _bg():
        async with SessionLocal() as s:
            try:
                await loader.run_etl(s, job_id, dry_run=False)
            except Exception as exc:  # noqa: BLE001
                await s.execute(
                    text(
                        """
                        UPDATE etl_jobs
                        SET status = 'attention', error_message = :err, completed_at = NOW()
                        WHERE id = :id
                        """
                    ),
                    {"id": job_id, "err": str(exc)},
                )
                await s.commit()

    asyncio.create_task(_bg())
    return job


@router.get("/jobs/{job_id}", response_model=EtlJobOut)
async def get_job(job_id: UUID, session: AsyncSession = Depends(get_session)):
    job = await loader.get_job(session, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.post("/jobs/{job_id}/cancel", response_model=EtlJobOut)
async def cancel(job_id: UUID, session: AsyncSession = Depends(get_session)):
    job = await loader.cancel_job(session, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job