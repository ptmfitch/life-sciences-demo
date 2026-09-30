#!/usr/bin/env bash
# beforeShellExecution: deny kubectl/terraform/psql aimed at a validated or prod target.
# Local development commands are allowed. Never returns "ask".
exec python3 -c "$(cat <<'PY'
from __future__ import annotations
import json
import re
import sys
from urllib.parse import urlparse

ENV_TOKENS = {"prod", "production", "validated"}
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}

TARGET_PATTERNS = (
    r"--context(?:=|\s+)(\S+)",
    r"use-context(?:\s+)(\S+)",
    r"--server(?:=|\s+)(\S+)",
    r"--cluster(?:=|\s+)(\S+)",
    r"(?:(?<=\s)|^)-h(?:=|\s*)(\S+)",
    r"--host(?:=|\s+)(\S+)",
    r"workspace\s+(?:select|new)\s+(\S+)",
    r"-var-file(?:=|\s+)(\S+)",
    r"TF_WORKSPACE=(\S+)",
    r"--backend-config(?:=|\s+)(\S+)",
    r"postgres(?:ql)?://\S+",
)


def clean(value: str) -> str:
    return value.strip().strip("'\"")


def tokens(value: str) -> set[str]:
    return {part.lower() for part in re.split(r"[^A-Za-z0-9]+", value) if part}


def is_env_target(value: str) -> bool:
    return bool(tokens(value) & ENV_TOKENS)


def host_of(value: str) -> str | None:
    text = clean(value)
    if "://" not in text:
        return None
    return urlparse(text).hostname


def emit(permission: str, message: str | None = None) -> None:
    payload: dict[str, str] = {"permission": permission}
    if message:
        payload["user_message"] = message
        payload["agent_message"] = message
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")


def main() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        emit(
            "deny",
            "Denied: the shell hook could not read its input, so the command is blocked.",
        )
        return

    command = str(data.get("command") or "")
    if not command.strip():
        emit("allow")
        return

    for pattern in TARGET_PATTERNS:
        for match in re.finditer(pattern, command, flags=re.IGNORECASE):
            captured = clean(match.group(0) if match.lastindex is None else match.group(1))
            host = host_of(captured)
            if host:
                if host.lower() in LOCAL_HOSTS:
                    continue
                if is_env_target(host):
                    emit(
                        "deny",
                        "Denied: this command targets a validated or production host. Local development commands are allowed.",
                    )
                    return
                continue
            if is_env_target(captured):
                emit(
                    "deny",
                    "Denied: this command targets a validated or production context or workspace. Local development commands are allowed.",
                )
                return

    emit("allow")


if __name__ == "__main__":
    main()
PY
)"
