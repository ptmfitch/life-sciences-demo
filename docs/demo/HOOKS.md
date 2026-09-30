DEMO / SYNTHETIC · for enablement only

# Repository hooks

Illustrative only. These hooks produce evidence for your validated process. They do not make the console validated.

Project hooks live in `.cursor/hooks.json`. Scripts run from the repository root.

## guard-validated-env.sh

Runs before a shell command that matches `kubectl`, `terraform`, or `psql`. The script reads the command and denies it when a context, workspace, var-file, or host is a validated or production target (`validated`, `prod`, or `production`). Local use is allowed, including `localhost` and `127.0.0.1`. The response is allow or deny. It never asks, because a cloud run has nobody to answer. This hook is set to fail closed.

The guard matches patterns in the command text. A bare `kubectl` on a production default context, or a command that only selects production through a `KUBECONFIG` override, can get through. This is a demo guardrail, not complete enforcement.

## deny-restricted-data.sh

Runs before a file read. The matcher for that event only sees the tool name, so the script checks `file_path` and any attachment path itself. It denies anything under a `restricted/` directory, any `*.phi` or `*.pii` file, and any `.env*` file. The response is allow or deny. It never asks. This hook is set to fail closed.

Restricted data stays out of the repository. There is no sample file for those paths. Cloud agents do not run hooks in their early read-only turns, which is why that data is not stored here for the hook to catch later.

## log-to-compliance.sh

Runs after a file edit and when the agent stops. It appends one JSON line to `audit_trail/agent-hooks.log`: a timestamp, the event name, a file path or a short summary, and the conversation id when the payload includes one. The log is gitignored. The script always allows the action and never blocks.

## Check

```bash
bash scripts/test-hooks.sh
```
