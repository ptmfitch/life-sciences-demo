import { useMemo, useState } from "react";
import { api } from "../lib/api";
import type { Run } from "../lib/types";
import { ErrorBoundary } from "../components/ErrorBoundary";
import { RunTile } from "../components/RunTile";

export function MonitorPage({
  runs,
  showToast,
}: {
  runs: Run[];
  showToast: (msg: string) => void;
}) {
  const [name, setName] = useState("");
  const [qty, setQty] = useState(3);
  const [busy, setBusy] = useState(false);

  const counts = useMemo(() => {
    const c = {
      active: 0,
      paused: 0,
      attention: 0,
      complete: 0,
      total: runs.length,
    };
    for (const r of runs) {
      if (r.status === "running") c.active += 1;
      if (r.status === "paused") c.paused += 1;
      if (r.status === "attention") c.attention += 1;
      if (r.status === "complete") c.complete += 1;
    }
    return c;
  }, [runs]);

  async function act(fn: () => Promise<unknown>, ok?: string) {
    setBusy(true);
    try {
      await fn();
      if (ok) showToast(ok);
    } catch (e) {
      showToast(e instanceof Error ? e.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <ErrorBoundary title="Monitor page error">
      <div className="space-y-6">
        <section className="rounded-2xl border border-line bg-card p-5 shadow-card">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold">Live monitoring</h2>
              <p className="mt-1 max-w-2xl text-sm text-muted">
                Start and control synthetic AstraLume BioTest Station runs. Visuals are
                illustrative — not scientifically validated.
              </p>
            </div>
            <div className="flex flex-wrap gap-2 text-xs">
              <Chip label="Active" value={counts.active} />
              <Chip label="Paused" value={counts.paused} />
              <Chip label="Attention" value={counts.attention} />
              <Chip label="Complete" value={counts.complete} />
              <Chip label="Total" value={counts.total} />
            </div>
          </div>

          <div className="mt-5 flex flex-wrap items-end gap-3">
            <label className="text-sm">
              <span className="mb-1 block text-xs text-muted">Test name</span>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Compound A - Rack 01"
                className="w-64 rounded-xl border border-line bg-canvas px-3 py-2"
              />
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-xs text-muted">Quantity</span>
              <input
                type="number"
                min={1}
                max={12}
                value={qty}
                onChange={(e) => setQty(Number(e.target.value))}
                className="w-20 rounded-xl border border-line bg-canvas px-3 py-2"
              />
            </label>
            <ToolbarBtn
              disabled={busy}
              onClick={() =>
                act(
                  () => api.createRuns({ test_name: name || undefined, quantity: 1 }),
                  "Test run added"
                )
              }
            >
              Add test run
            </ToolbarBtn>
            <ToolbarBtn
              disabled={busy}
              onClick={() =>
                act(
                  () =>
                    api.createRuns({
                      test_name: name || undefined,
                      quantity: qty,
                    }),
                  `Added ${qty} runs`
                )
              }
            >
              Add multiple
            </ToolbarBtn>
            <ToolbarBtn disabled={busy} onClick={() => act(() => api.bulk("start_all"))}>
              Start all pending
            </ToolbarBtn>
            <ToolbarBtn disabled={busy} onClick={() => act(() => api.bulk("pause_all"))}>
              Pause all running
            </ToolbarBtn>
            <ToolbarBtn disabled={busy} onClick={() => act(() => api.bulk("stop_all"))}>
              Stop all active
            </ToolbarBtn>
            <ToolbarBtn
              disabled={busy}
              onClick={() => act(() => api.bulk("clear_completed"), "Cleared completed")}
            >
              Clear completed
            </ToolbarBtn>
            <ToolbarBtn
              disabled={busy}
              tone="danger"
              onClick={() => {
                if (window.confirm("Clear all tests? This cannot be undone.")) {
                  act(() => api.bulk("clear_all"), "All tests cleared");
                }
              }}
            >
              Clear all
            </ToolbarBtn>
          </div>
        </section>

        {runs.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-line bg-card p-12 text-center">
            <h3 className="text-lg font-medium">No test runs yet</h3>
            <p className="mt-2 text-sm text-muted">
              Add a named test run to see a live monitoring tile appear.
            </p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {runs.map((run) => (
              <RunTile
                key={run.id}
                run={run}
                onAction={(id, action) => {
                  const map: Record<string, () => Promise<unknown>> = {
                    start: () => api.start(id),
                    pause: () => api.pause(id),
                    resume: () => api.resume(id),
                    stop: () => api.stop(id),
                    restart: () => api.restart(id),
                    clear: () => api.clear(id),
                  };
                  act(map[action]);
                }}
              />
            ))}
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}

function Chip({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-full border border-line bg-canvas px-3 py-1">
      <span className="text-muted">{label}</span>{" "}
      <span className="font-semibold text-ink">{value}</span>
    </div>
  );
}

function ToolbarBtn({
  children,
  onClick,
  disabled,
  tone = "default",
}: {
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  tone?: "default" | "danger";
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`rounded-xl border px-3 py-2 text-sm font-medium disabled:opacity-50 ${
        tone === "danger"
          ? "border-rose-200 bg-rose-50 text-failed"
          : "border-line bg-canvas text-ink hover:bg-accentSoft hover:text-accent"
      }`}
    >
      {children}
    </button>
  );
}