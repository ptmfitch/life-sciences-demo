"""In-process SSE event broker."""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict, deque
from typing import Any
from uuid import UUID


class EventBroker:
    def __init__(self, buffer_size: int = 300):
        self._subscribers: set[asyncio.Queue] = set()
        self._buffers: dict[UUID, deque[dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=buffer_size)
        )
        self._latest: dict[UUID, dict[str, Any]] = {}
        self._wells: dict[UUID, list[dict[str, Any]]] = {}
        self._sparkline: dict[UUID, deque[float]] = defaultdict(lambda: deque(maxlen=60))

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=500)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._subscribers.discard(queue)

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        message = {"type": event_type, "data": payload}
        dead: list[asyncio.Queue] = []
        for queue in self._subscribers:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                dead.append(queue)
        for queue in dead:
            self._subscribers.discard(queue)

    def record_telemetry(self, run_id: UUID, reading: dict[str, Any]) -> None:
        clean = {k: v for k, v in reading.items() if k not in ("wells", "_duplicate_candidate")}
        self._buffers[run_id].append(clean)
        self._latest[run_id] = clean
        if reading.get("wells"):
            self._wells[run_id] = reading["wells"]
        activity = reading.get("activity_index")
        if activity is not None:
            self._sparkline[run_id].append(float(activity))

    def clear_run(self, run_id: UUID) -> None:
        self._buffers.pop(run_id, None)
        self._latest.pop(run_id, None)
        self._wells.pop(run_id, None)
        self._sparkline.pop(run_id, None)

    def snapshot(self, runs: list[dict[str, Any]]) -> dict[str, Any]:
        enriched = []
        for run in runs:
            rid = run["id"] if isinstance(run["id"], UUID) else UUID(str(run["id"]))
            item = dict(run)
            item["latest"] = self._latest.get(rid)
            item["wells"] = self._wells.get(rid)
            item["sparkline"] = list(self._sparkline.get(rid, []))
            enriched.append(item)
        return {"runs": enriched}

    def get_latest(self, run_id: UUID) -> dict[str, Any] | None:
        return self._latest.get(run_id)

    def get_wells(self, run_id: UUID) -> list[dict[str, Any]] | None:
        return self._wells.get(run_id)

    def get_sparkline(self, run_id: UUID) -> list[float]:
        return list(self._sparkline.get(run_id, []))


broker = EventBroker()


def sse_format(event_type: str, data: Any) -> str:
    body = json.dumps(data, default=str)
    return f"event: {event_type}\ndata: {body}\n\n"