#!/usr/bin/env bash
# beforeReadFile: the matcher only sees the tool name, so the path check is here.
# Denies restricted/, *.phi, *.pii, and .env*. Never returns "ask".
exec python3 -c "$(cat <<'PY'
from __future__ import annotations
import fnmatch
import json
import sys


def emit(permission: str, message: str | None = None) -> None:
    payload: dict[str, str] = {"permission": permission}
    if message:
        payload["user_message"] = message
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")


def is_restricted(path: str) -> bool:
    if not path or not str(path).strip():
        return True
    normalized = str(path).replace("\\", "/")
    parts = [part for part in normalized.split("/") if part not in ("", ".")]
    if "restricted" in parts:
        return True
    base = parts[-1] if parts else ""
    lowered = base.lower()
    if lowered.endswith(".phi") or lowered.endswith(".pii"):
        return True
    if fnmatch.fnmatch(base, ".env*") or fnmatch.fnmatch(lowered, ".env*"):
        return True
    return False


def paths_from(data: dict) -> list[str]:
    found: list[str] = []
    file_path = data.get("file_path")
    if isinstance(file_path, str):
        found.append(file_path)
    elif file_path is not None:
        found.append(str(file_path))
    else:
        found.append("")
    for attachment in data.get("attachments") or []:
        if isinstance(attachment, dict) and attachment.get("file_path"):
            found.append(str(attachment["file_path"]))
    return found


def main() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        emit(
            "deny",
            "Denied: the read hook could not read its input, so the read is blocked.",
        )
        return

    if not isinstance(data, dict):
        emit("deny", "Denied: the read hook received an unexpected payload.")
        return

    denied = [path for path in paths_from(data) if is_restricted(path)]
    if denied:
        emit(
            "deny",
            "Denied: that path is restricted (.env*, restricted/, .phi, or .pii). Restricted data is not kept in this repository.",
        )
        return
    emit("allow")


if __name__ == "__main__":
    main()
PY
)"
