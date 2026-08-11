"""Scan telemetry directory for CSV files."""

from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _count_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        next(reader, None)
        return sum(1 for _ in reader)


def _peek_meta(path: Path) -> dict[str, str | None]:
    meta = {"test_name": None, "device_id": None, "assay_run_id": None}
    try:
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            row = next(reader, None)
            if row:
                meta["test_name"] = row.get("test_name")
                meta["device_id"] = row.get("device_id")
                meta["assay_run_id"] = row.get("assay_run_id")
    except OSError:
        pass
    return meta


async def scan_directory(session: AsyncSession) -> dict[str, Any]:
    directory = settings.telemetry_path
    directory.mkdir(parents=True, exist_ok=True)
    files_out: list[dict[str, Any]] = []
    total_rows = 0
    newest: datetime | None = None

    csv_files = sorted(directory.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in csv_files:
        try:
            sha = _file_sha256(path)
            rows = _count_rows(path)
            meta = _peek_meta(path)
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if newest is None or mtime > newest:
                newest = mtime
            total_rows += rows

            existing = await session.execute(
                text("SELECT id, ingestion_status, sha256 FROM source_files WHERE filename = :f"),
                {"f": path.name},
            )
            row = existing.mappings().first()
            if row:
                file_id = row["id"]
                status = row["ingestion_status"]
                if row["sha256"] != sha and status == "ingested":
                    status = "changed"
                    await session.execute(
                        text(
                            """
                            UPDATE source_files
                            SET sha256 = :sha, size_bytes = :size, row_count = :rows,
                                ingestion_status = 'changed', filepath = :fp,
                                test_name = :tn, device_id = :did, assay_run_id = :aid
                            WHERE id = :id
                            """
                        ),
                        {
                            "id": file_id,
                            "sha": sha,
                            "size": path.stat().st_size,
                            "rows": rows,
                            "fp": str(path),
                            "tn": meta["test_name"],
                            "did": meta["device_id"],
                            "aid": meta["assay_run_id"],
                        },
                    )
                else:
                    await session.execute(
                        text(
                            """
                            UPDATE source_files
                            SET size_bytes = :size, row_count = :rows, filepath = :fp,
                                test_name = :tn, device_id = :did, assay_run_id = :aid
                            WHERE id = :id
                            """
                        ),
                        {
                            "id": file_id,
                            "size": path.stat().st_size,
                            "rows": rows,
                            "fp": str(path),
                            "tn": meta["test_name"],
                            "did": meta["device_id"],
                            "aid": meta["assay_run_id"],
                        },
                    )
            else:
                file_id = uuid4()
                status = "pending"
                await session.execute(
                    text(
                        """
                        INSERT INTO source_files (
                            id, filename, filepath, sha256, size_bytes, row_count,
                            test_name, device_id, assay_run_id, ingestion_status
                        ) VALUES (
                            :id, :fn, :fp, :sha, :size, :rows, :tn, :did, :aid, 'pending'
                        )
                        """
                    ),
                    {
                        "id": file_id,
                        "fn": path.name,
                        "fp": str(path),
                        "sha": sha,
                        "size": path.stat().st_size,
                        "rows": rows,
                        "tn": meta["test_name"],
                        "did": meta["device_id"],
                        "aid": meta["assay_run_id"],
                    },
                )

            files_out.append(
                {
                    "id": str(file_id),
                    "filename": path.name,
                    "filepath": str(path),
                    "sha256": sha,
                    "size_bytes": path.stat().st_size,
                    "row_count": rows,
                    "test_name": meta["test_name"],
                    "device_id": meta["device_id"],
                    "assay_run_id": meta["assay_run_id"],
                    "ingestion_status": status,
                    "modified_at": mtime.isoformat(),
                }
            )
        except OSError as exc:
            files_out.append(
                {
                    "id": None,
                    "filename": path.name,
                    "error": str(exc),
                    "ingestion_status": "error",
                }
            )

    await session.commit()
    return {
        "directory": str(directory),
        "file_count": len(files_out),
        "total_rows": total_rows,
        "newest_file_timestamp": newest,
        "files": files_out,
    }