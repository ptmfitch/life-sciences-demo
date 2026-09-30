#!/usr/bin/env bash
# Pipe sample hook payloads and check allow/deny. Illustrative only.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GUARD="$ROOT/.cursor/hooks/guard-validated-env.sh"
DENY="$ROOT/.cursor/hooks/deny-restricted-data.sh"
LOG="$ROOT/.cursor/hooks/log-to-compliance.sh"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

permission_of() {
  python3 -c 'import json,sys; print(json.load(sys.stdin)["permission"])'
}

run_perm() {
  local script="$1"
  local expected="$2"
  local payload="$3"
  local out perm
  out="$(printf '%s' "$payload" | "$script")"
  perm="$(printf '%s' "$out" | permission_of)"
  if [[ "$perm" != "$expected" ]]; then
    fail "$script expected $expected, got $perm. payload=$payload output=$out"
  fi
  if [[ "$perm" == "ask" || "$out" == *'"permission": "ask"'* || "$out" == *'"permission":"ask"'* ]]; then
    fail "$script returned ask"
  fi
}

shell_payload() {
  python3 -c 'import json,sys; print(json.dumps({"hook_event_name":"beforeShellExecution","conversation_id":"conv-test","command":sys.argv[1],"cwd":"/workspace","sandbox":False}))' "$1"
}

read_payload() {
  python3 -c 'import json,sys; print(json.dumps({"hook_event_name":"beforeReadFile","conversation_id":"conv-test","file_path":sys.argv[1],"content":"","attachments":json.loads(sys.argv[2])}))' "$1" "$2"
}

echo "guard-validated-env.sh"
run_perm "$GUARD" allow "$(shell_payload "psql -h 127.0.0.1 -U biotest -d biotest")"
run_perm "$GUARD" allow "$(shell_payload "psql -h localhost -d biotest")"
run_perm "$GUARD" allow "$(shell_payload "psql postgresql://biotest:biotest@127.0.0.1:5432/biotest")"
run_perm "$GUARD" allow "$(shell_payload "psql -h localhost -c \"select * from products\"")"
run_perm "$GUARD" allow "$(shell_payload "kubectl --context minikube get pods")"
run_perm "$GUARD" allow "$(shell_payload "kubectl config use-context docker-desktop")"
run_perm "$GUARD" allow "$(shell_payload "terraform workspace select dev")"
run_perm "$GUARD" allow "$(shell_payload "terraform apply -var-file=dev.tfvars")"
run_perm "$GUARD" deny "$(shell_payload "kubectl --context prod get pods")"
run_perm "$GUARD" deny "$(shell_payload "kubectl --context=validated-cluster get ns")"
run_perm "$GUARD" deny "$(shell_payload "kubectl config use-context production")"
run_perm "$GUARD" deny "$(shell_payload "psql -h prod-db.internal.example -U app")"
run_perm "$GUARD" deny "$(shell_payload "psql -h validated-db.internal -d app")"
run_perm "$GUARD" deny "$(shell_payload "psql postgresql://user:pass@prod-db.example.com:5432/app")"
run_perm "$GUARD" deny "$(shell_payload "terraform workspace select prod")"
run_perm "$GUARD" deny "$(shell_payload "terraform workspace select validated")"
run_perm "$GUARD" deny "$(shell_payload "terraform apply -var-file=environments/prod.tfvars")"
run_perm "$GUARD" deny "$(printf '%s' 'not-json')"

echo "deny-restricted-data.sh"
run_perm "$DENY" allow "$(read_payload "$ROOT/README.md" "[]")"
run_perm "$DENY" allow "$(read_payload "$ROOT/server/app/validated/acceptance.py" "[]")"
run_perm "$DENY" deny "$(read_payload "$ROOT/restricted/notes.txt" "[]")"
run_perm "$DENY" deny "$(read_payload "$ROOT/lab/subject.phi" "[]")"
run_perm "$DENY" deny "$(read_payload "$ROOT/lab/subject.pii" "[]")"
run_perm "$DENY" deny "$(read_payload "$ROOT/.env" "[]")"
run_perm "$DENY" deny "$(read_payload "$ROOT/.env.local" "[]")"
run_perm "$DENY" deny "$(read_payload "$ROOT/.env.example" "[]")"
run_perm "$DENY" deny "$(read_payload "$ROOT/README.md" "[{\"type\":\"file\",\"file_path\":\"$ROOT/.env\"}]")"
run_perm "$DENY" deny "$(printf '%s' 'not-json')"

echo "log-to-compliance.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export CURSOR_PROJECT_DIR="$TMP"
EDIT_PAYLOAD="$(python3 -c 'import json; print(json.dumps({"hook_event_name":"afterFileEdit","conversation_id":"conv-edit","file_path":"/workspace/README.md","edits":[{"old_string":"SECRET_SENTINEL_OLD","new_string":"next"}]}))')"
STOP_PAYLOAD="$(python3 -c 'import json; print(json.dumps({"hook_event_name":"stop","conversation_id":"conv-stop","status":"completed","loop_count":0}))')"
EDIT_OUT="$(printf '%s' "$EDIT_PAYLOAD" | "$LOG")"
STOP_OUT="$(printf '%s' "$STOP_PAYLOAD" | "$LOG")"
printf '%s' "$EDIT_OUT" | python3 -c 'import json,sys; data=json.load(sys.stdin); assert data=={}, data; assert "followup_message" not in data'
printf '%s' "$STOP_OUT" | python3 -c 'import json,sys; data=json.load(sys.stdin); assert data=={}, data; assert "followup_message" not in data'
python3 - "$TMP/audit_trail/agent-hooks.log" <<'PY'
import json
import sys

path = sys.argv[1]
lines = open(path, encoding="utf-8").read().splitlines()
if len(lines) != 2:
    raise SystemExit(f"expected 2 log lines, got {len(lines)}")
edit = json.loads(lines[0])
stop = json.loads(lines[1])
for record in (edit, stop):
    if not record.get("timestamp"):
        raise SystemExit(f"missing timestamp: {record}")
if edit.get("event") != "afterFileEdit":
    raise SystemExit(edit)
if edit.get("file_path") != "/workspace/README.md":
    raise SystemExit(edit)
if edit.get("conversation_id") != "conv-edit":
    raise SystemExit(edit)
if "SECRET_SENTINEL_OLD" in lines[0]:
    raise SystemExit("log stored edit contents")
if stop.get("event") != "stop":
    raise SystemExit(stop)
if stop.get("conversation_id") != "conv-stop":
    raise SystemExit(stop)
if "status=completed" not in stop.get("summary", ""):
    raise SystemExit(stop)
print("log lines ok")
PY

if ! grep -q 'audit_trail/agent-hooks.log' "$ROOT/.gitignore"; then
  fail "gitignore is missing audit_trail/agent-hooks.log"
fi

echo "OK: hook scripts"
