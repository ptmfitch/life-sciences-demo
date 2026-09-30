#!/usr/bin/env bash
# afterFileEdit and stop: append one JSON line and always allow.
exec python3 -c "$(cat <<'PY'
import json
import os
import sys
from datetime import datetime, timezone


def emit_allow() -> None:
    json.dump({}, sys.stdout)
    sys.stdout.write("\n")


def event_name(data: dict) -> str:
    name = data.get("hook_event_name")
    if isinstance(name, str) and name.strip():
        return name
    if "status" in data and "file_path" not in data:
        return "stop"
    if "file_path" in data or "edits" in data:
        return "afterFileEdit"
    return "unknown"


def summary_for(data: dict, event: str) -> str | None:
    if event == "stop" or ("status" in data and "file_path" not in data):
        status = data.get("status", "")
        loop_count = data.get("loop_count", "")
        return f"status={status} loop_count={loop_count}"
    return None


def main() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        data = {}
    if not isinstance(data, dict):
        data = {}

    event = event_name(data)
    record: dict[str, str] = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": event,
    }
    file_path = data.get("file_path")
    if isinstance(file_path, str) and file_path:
        record["file_path"] = file_path
    else:
        summary = summary_for(data, event)
        if summary:
            record["summary"] = summary
    conversation_id = data.get("conversation_id")
    if isinstance(conversation_id, str) and conversation_id:
        record["conversation_id"] = conversation_id

    root = os.environ.get("CURSOR_PROJECT_DIR") or os.getcwd()
    log_path = os.path.join(root, "audit_trail", "agent-hooks.log")
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")
    except OSError:
        pass

    emit_allow()


if __name__ == "__main__":
    main()
PY
)"
