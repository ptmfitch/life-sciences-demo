"""In-process asyncio run manager for synthetic assay runs."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import SessionLocal
from app.runs.events import EventBroker
from app.sim.simulator import RunIdentity, Simulator, regime_for_compound
from app.sim.writer import build_filename, maybe_duplicate_row, write_csv

logger = logging.getLogger(__name__)

COMPOUND_CODES = ["CMP-A01", "CMP-B02", "CMP-C03", "CMP-D04", "CMP-E05"]


class RunManager:
    def __init__(self, broker: EventBroker):
        self.broker = broker
        self._tasks: dict[UUID, asyncio.Task] = {}
        self._pause_events: dict[UUID, asyncio.Event] = {}
        self._row_buffers: dict[UUID, list[dict[str, Any]]] = {}
        self._started_at: dict[UUID, datetime] = {}
        self._lock = asyncio.Lock()

    async def startup(self, session: AsyncSession) -> None:
        # Interrupt any mid-flight ETL jobs
        await session.execute(
            text(
                """
                UPDATE etl_jobs
                SET status = 'interrupted', completed_at = NOW(),
                    error_message = 'Server restarted during job'
                WHERE status IN ('running', 'pending')
                """
            )
        )
        result = await session.execute(
            text(
                """
                SELECT id, test_name, device_id, rack_id, assay_run_id, compound_code,
                       well_count, seed, tick_index, status, started_at
                FROM test_runs
                WHERE status IN ('running', 'paused')
                """
            )
        )
        rows = result.mappings().all()
        await session.commit()

        for row in rows:
            run_id = row["id"]
            try:
                if row["started_at"]:
                    self._started_at[run_id] = row["started_at"].replace(tzinfo=timezone.utc) if row["started_at"].tzinfo is None else row["started_at"]
                await self._spawn_task(
                    run_id=run_id,
                    identity=RunIdentity(
                        test_name=row["test_name"],
                        device_id=row["device_id"],
                        rack_id=row["rack_id"],
                        assay_run_id=row["assay_run_id"],
                        compound_code=row["compound_code"],
                        well_count=row["well_count"],
                        seed=row["seed"],
                        regime=regime_for_compound(row["compound_code"]),
                    ),
                    start_tick=row["tick_index"],
                    initially_paused=(row["status"] == "paused"),
                )
                logger.info("Resumed run %s from tick %s", run_id, row["tick_index"])
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to resume run %s", run_id)
                async with SessionLocal() as s:
                    await s.execute(
                        text(
                            """
                            UPDATE test_runs
                            SET status = 'interrupted', error_message = :err, updated_at = NOW()
                            WHERE id = :id
                            """
                        ),
                        {"id": run_id, "err": str(exc)},
                    )
                    await s.commit()

    async def shutdown(self) -> None:
        for run_id, task in list(self._tasks.items()):
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()

    async def create_runs(
        self,
        session: AsyncSession,
        *,
        test_name: str | None,
        quantity: int,
        device_id: str | None,
        rack_id: str | None,
        assay_run_id: str | None,
        compound_code: str | None,
        well_count: int,
        seed: int | None,
    ) -> list[dict[str, Any]]:
        created = []
        base_seed = seed if seed is not None else settings.seed
        for i in range(quantity):
            rid = uuid4()
            idx = await self._next_index(session)
            name = test_name or f"Compound {chr(65 + (idx % 26))} - Rack {(idx % 12) + 1:02d}"
            if quantity > 1 and test_name:
                name = f"{test_name} #{i + 1}"
            elif quantity > 1 and not test_name:
                name = f"Compound {chr(65 + ((idx + i) % 26))} - Rack {((idx + i) % 12) + 1:02d}"

            did = device_id or f"ALBT-{(idx + i) % 100:03d}"
            if quantity > 1 and device_id is None:
                did = f"ALBT-{(idx + i) % 100:03d}"

            rack = rack_id or f"RACK-{(idx + i) % 20 + 1:02d}"
            assay = assay_run_id or f"AR-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{idx + i:04d}"
            if quantity > 1 and assay_run_id:
                assay = f"{assay_run_id}-{i + 1}"

            compound = compound_code or COMPOUND_CODES[(idx + i) % len(COMPOUND_CODES)]
            run_seed = base_seed + i * 17 + idx

            await session.execute(
                text(
                    """
                    INSERT INTO test_runs (
                        id, test_name, device_id, rack_id, assay_run_id, compound_code,
                        well_count, status, seed, output_dir
                    ) VALUES (
                        :id, :test_name, :device_id, :rack_id, :assay_run_id, :compound_code,
                        :well_count, 'pending', :seed, :output_dir
                    )
                    """
                ),
                {
                    "id": rid,
                    "test_name": name,
                    "device_id": did,
                    "rack_id": rack,
                    "assay_run_id": assay,
                    "compound_code": compound,
                    "well_count": well_count,
                    "seed": run_seed,
                    "output_dir": str(settings.telemetry_path),
                },
            )
            created.append(await self.get_run(session, rid))
        await session.commit()
        for run in created:
            await self.broker.publish("run_state", run)
        return created

    async def _next_index(self, session: AsyncSession) -> int:
        result = await session.execute(text("SELECT COUNT(*) FROM test_runs"))
        return int(result.scalar_one())

    async def list_runs(self, session: AsyncSession) -> list[dict[str, Any]]:
        result = await session.execute(
            text("SELECT * FROM test_runs ORDER BY created_at DESC")
        )
        return [self._enrich(dict(r)) for r in result.mappings().all()]

    async def get_run(self, session: AsyncSession, run_id: UUID) -> dict[str, Any] | None:
        result = await session.execute(
            text("SELECT * FROM test_runs WHERE id = :id"), {"id": run_id}
        )
        row = result.mappings().first()
        return self._enrich(dict(row)) if row else None

    def _enrich(self, row: dict[str, Any]) -> dict[str, Any]:
        rid = row["id"]
        row["elapsed_seconds"] = int(row.get("tick_index") or 0)
        row["latest"] = self.broker.get_latest(rid)
        row["wells"] = self.broker.get_wells(rid)
        row["sparkline"] = self.broker.get_sparkline(rid)
        return row

    async def start(self, session: AsyncSession, run_id: UUID) -> dict[str, Any]:
        run = await self.get_run(session, run_id)
        if not run:
            raise KeyError("Run not found")
        if run["status"] in ("running", "paused"):
            return run

        active = sum(1 for t in self._tasks.values() if not t.done())
        if active >= settings.max_concurrent_runs:
            raise RuntimeError(f"Max concurrent runs ({settings.max_concurrent_runs}) reached")

        identity = RunIdentity(
            test_name=run["test_name"],
            device_id=run["device_id"],
            rack_id=run["rack_id"],
            assay_run_id=run["assay_run_id"],
            compound_code=run["compound_code"],
            well_count=run["well_count"],
            seed=run["seed"],
            regime=regime_for_compound(run["compound_code"]),
        )
        now = datetime.now(timezone.utc)
        self._started_at[run_id] = now
        await session.execute(
            text(
                """
                UPDATE test_runs
                SET status = 'running', started_at = :now, completed_at = NULL,
                    error_message = NULL, updated_at = :now
                WHERE id = :id
                """
            ),
            {"id": run_id, "now": now},
        )
        await session.commit()
        await self._spawn_task(run_id, identity, start_tick=run["tick_index"], initially_paused=False)
        run = await self.get_run(session, run_id)
        await self.broker.publish("run_state", run)
        return run

    async def pause(self, session: AsyncSession, run_id: UUID) -> dict[str, Any]:
        event = self._pause_events.get(run_id)
        if event:
            event.clear()
        now = datetime.now(timezone.utc)
        await session.execute(
            text(
                """
                UPDATE test_runs
                SET status = 'paused', paused_at = :now, updated_at = :now
                WHERE id = :id AND status = 'running'
                """
            ),
            {"id": run_id, "now": now},
        )
        await session.commit()
        run = await self.get_run(session, run_id)
        await self.broker.publish("run_state", run)
        return run

    async def resume(self, session: AsyncSession, run_id: UUID) -> dict[str, Any]:
        event = self._pause_events.get(run_id)
        if event:
            event.set()
        now = datetime.now(timezone.utc)
        await session.execute(
            text(
                """
                UPDATE test_runs
                SET status = 'running', paused_at = NULL, updated_at = :now
                WHERE id = :id AND status = 'paused'
                """
            ),
            {"id": run_id, "now": now},
        )
        await session.commit()
        # If task died, re-spawn
        task = self._tasks.get(run_id)
        if not task or task.done():
            run = await self.get_run(session, run_id)
            if run:
                identity = RunIdentity(
                    test_name=run["test_name"],
                    device_id=run["device_id"],
                    rack_id=run["rack_id"],
                    assay_run_id=run["assay_run_id"],
                    compound_code=run["compound_code"],
                    well_count=run["well_count"],
                    seed=run["seed"],
                    regime=regime_for_compound(run["compound_code"]),
                )
                await self._spawn_task(run_id, identity, start_tick=run["tick_index"], initially_paused=False)
        run = await self.get_run(session, run_id)
        await self.broker.publish("run_state", run)
        return run

    async def stop(self, session: AsyncSession, run_id: UUID) -> dict[str, Any]:
        task = self._tasks.get(run_id)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        now = datetime.now(timezone.utc)
        await session.execute(
            text(
                """
                UPDATE test_runs
                SET status = 'stopped', completed_at = :now, updated_at = :now
                WHERE id = :id AND status NOT IN ('complete', 'stopped')
                """
            ),
            {"id": run_id, "now": now},
        )
        await session.commit()
        run = await self.get_run(session, run_id)
        await self.broker.publish("run_state", run)
        return run

    async def restart(self, session: AsyncSession, run_id: UUID) -> dict[str, Any]:
        await self.stop(session, run_id)
        await session.execute(
            text(
                """
                UPDATE test_runs
                SET tick_index = 0, row_count = 0, file_count = 0,
                    started_at = NULL, completed_at = NULL, last_reading_at = NULL,
                    error_message = NULL, status = 'pending', updated_at = NOW()
                WHERE id = :id
                """
            ),
            {"id": run_id},
        )
        await session.commit()
        self.broker.clear_run(run_id)
        self._row_buffers.pop(run_id, None)
        self._started_at.pop(run_id, None)
        return await self.start(session, run_id)

    async def clear(self, session: AsyncSession, run_id: UUID) -> None:
        await self.stop(session, run_id)
        await session.execute(text("DELETE FROM test_runs WHERE id = :id"), {"id": run_id})
        await session.commit()
        self.broker.clear_run(run_id)
        self._row_buffers.pop(run_id, None)
        self._started_at.pop(run_id, None)
        self._tasks.pop(run_id, None)
        self._pause_events.pop(run_id, None)
        await self.broker.publish("run_state", {"id": str(run_id), "status": "cleared"})

    async def bulk(self, session: AsyncSession, action: str) -> list[dict[str, Any]]:
        runs = await self.list_runs(session)
        if action == "start_all":
            for run in runs:
                if run["status"] in ("pending", "stopped", "interrupted"):
                    try:
                        await self.start(session, run["id"])
                    except RuntimeError:
                        break
        elif action == "pause_all":
            for run in runs:
                if run["status"] == "running":
                    await self.pause(session, run["id"])
        elif action == "stop_all":
            for run in runs:
                if run["status"] in ("running", "paused"):
                    await self.stop(session, run["id"])
        elif action == "clear_completed":
            for run in runs:
                if run["status"] in ("complete", "stopped", "interrupted"):
                    await self.clear(session, run["id"])
        elif action == "clear_all":
            for run in runs:
                await self.clear(session, run["id"])
        return await self.list_runs(session)

    async def _spawn_task(
        self,
        run_id: UUID,
        identity: RunIdentity,
        start_tick: int,
        initially_paused: bool,
    ) -> None:
        async with self._lock:
            old = self._tasks.get(run_id)
            if old and not old.done():
                return
            pause_event = asyncio.Event()
            if initially_paused:
                pause_event.clear()
            else:
                pause_event.set()
            self._pause_events[run_id] = pause_event
            self._row_buffers.setdefault(run_id, [])
            task = asyncio.create_task(
                self._run_loop(run_id, identity, start_tick),
                name=f"run-{run_id}",
            )
            self._tasks[run_id] = task

    async def _run_loop(self, run_id: UUID, identity: RunIdentity, start_tick: int) -> None:
        sim = Simulator(identity)
        tick = start_tick
        max_ticks = settings.max_runtime_minutes * 60
        pause_event = self._pause_events[run_id]
        started = self._started_at.get(run_id) or datetime.now(timezone.utc)
        self._started_at[run_id] = started

        try:
            while tick < max_ticks:
                await pause_event.wait()
                reading = sim.reading_at(tick, started_at=started)
                # Drop ephemeral keys before buffering for CSV
                csv_row = {k: v for k, v in reading.items() if k != "wells"}
                self._row_buffers[run_id].append(csv_row)
                self.broker.record_telemetry(run_id, reading)

                now = datetime.now(timezone.utc)
                payload = {
                    "run_id": str(run_id),
                    "reading": {k: v for k, v in reading.items() if k != "_duplicate_candidate"},
                    "tick_index": tick,
                }
                await self.broker.publish("telemetry", payload)

                # Checkpoint every CSV flush and also lightly every tick for last_reading
                async with SessionLocal() as session:
                    await session.execute(
                        text(
                            """
                            UPDATE test_runs
                            SET tick_index = :tick, row_count = row_count + 1,
                                last_reading_at = :now, updated_at = :now,
                                status = CASE WHEN status = 'paused' THEN 'paused' ELSE 'running' END
                            WHERE id = :id
                            """
                        ),
                        {"id": run_id, "tick": tick + 1, "now": now},
                    )
                    await session.commit()

                if len(self._row_buffers[run_id]) >= settings.rows_per_file:
                    await self._flush_csv(run_id, identity)

                await self.broker.publish(
                    "run_state",
                    {
                        "id": str(run_id),
                        "status": "paused" if not pause_event.is_set() else "running",
                        "tick_index": tick + 1,
                        "row_count": None,
                        "last_reading_at": now.isoformat(),
                        "latest": self.broker.get_latest(run_id),
                        "wells": self.broker.get_wells(run_id),
                        "sparkline": self.broker.get_sparkline(run_id),
                        "elapsed_seconds": tick + 1,
                    },
                )

                tick += 1
                await asyncio.sleep(settings.tick_interval_seconds)

            # Complete
            await self._flush_csv(run_id, identity, force=True)
            async with SessionLocal() as session:
                await session.execute(
                    text(
                        """
                        UPDATE test_runs
                        SET status = 'complete', completed_at = NOW(), updated_at = NOW()
                        WHERE id = :id
                        """
                    ),
                    {"id": run_id},
                )
                await session.commit()
                run = await self.get_run(session, run_id)
                await self.broker.publish("run_state", run)
        except asyncio.CancelledError:
            await self._flush_csv(run_id, identity, force=True)
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("Run %s failed", run_id)
            await self._flush_csv(run_id, identity, force=True)
            async with SessionLocal() as session:
                await session.execute(
                    text(
                        """
                        UPDATE test_runs
                        SET status = 'attention', error_message = :err, updated_at = NOW()
                        WHERE id = :id
                        """
                    ),
                    {"id": run_id, "err": str(exc)},
                )
                await session.commit()
                run = await self.get_run(session, run_id)
                await self.broker.publish("run_state", run)

    async def _flush_csv(
        self, run_id: UUID, identity: RunIdentity, force: bool = False
    ) -> None:
        buf = self._row_buffers.get(run_id, [])
        if not buf:
            return
        if not force and len(buf) < settings.rows_per_file:
            return

        chunk = buf[: settings.rows_per_file] if not force else list(buf)
        if not force:
            self._row_buffers[run_id] = buf[settings.rows_per_file :]
        else:
            self._row_buffers[run_id] = []

        rows = maybe_duplicate_row(chunk)
        when = datetime.now(timezone.utc)
        path = settings.telemetry_path / build_filename(
            identity.test_name, identity.device_id, when
        )

        def _write() -> None:
            write_csv(path, rows)

        await asyncio.to_thread(_write)
        logger.info(
            "Wrote CSV run_id=%s device=%s path=%s rows=%s",
            run_id,
            identity.device_id,
            path,
            len(rows),
        )
        async with SessionLocal() as session:
            await session.execute(
                text(
                    """
                    UPDATE test_runs
                    SET file_count = file_count + 1, updated_at = NOW()
                    WHERE id = :id
                    """
                ),
                {"id": run_id},
            )
            await session.commit()
            await self.broker.publish(
                "file_written",
                {"run_id": str(run_id), "filename": path.name, "rows": len(rows)},
            )