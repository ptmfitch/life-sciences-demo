import { useEffect, useMemo, useRef, useState } from "react";
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
  const [clearOpen, setClearOpen] = useState(false);
  const clearMenuRef = useRef<HTMLDivElement>(null);

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

  useEffect(() => {
    if (!clearOpen) return;
    function onPointerDown(e: PointerEvent) {
      if (clearMenuRef.current && !clearMenuRef.current.contains(e.target as Node)) {
        setClearOpen(false);
      }
    }
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setClearOpen(false);
    }
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [clearOpen]);

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
            <IconBtn
              label={`Add ${qty} test run${qty === 1 ? "" : "s"}`}
              disabled={busy}
              onClick={() =>
                act(
                  () =>
                    api.createRuns({
                      test_name: name || undefined,
                      quantity: qty,
                    }),
                  `Added ${qty} run${qty === 1 ? "" : "s"}`
                )
              }
            >
              <IconPlus />
            </IconBtn>
            <IconBtn
              label="Start all pending"
              disabled={busy}
              onClick={() => act(() => api.bulk("start_all"))}
            >
              <IconPlay />
            </IconBtn>
            <IconBtn
              label="Pause all running"
              disabled={busy}
              onClick={() => act(() => api.bulk("pause_all"))}
            >
              <IconPause />
            </IconBtn>
            <IconBtn
              label="Stop all active"
              disabled={busy}
              onClick={() => act(() => api.bulk("stop_all"))}
            >
              <IconStop />
            </IconBtn>
            <div className="relative" ref={clearMenuRef}>
              <IconBtn
                label="Clear options"
                disabled={busy}
                tone="danger"
                wide
                onClick={() => setClearOpen((o) => !o)}
                aria-haspopup="menu"
                aria-expanded={clearOpen}
              >
                <span className="inline-flex items-center gap-0.5">
                  <IconTrash />
                  <IconChevronDown />
                </span>
              </IconBtn>
              {clearOpen ? (
                <div
                  role="menu"
                  className="absolute right-0 z-10 mt-1 min-w-[10.5rem] rounded-xl border border-line bg-card py-1 shadow-card"
                >
                  <button
                    type="button"
                    role="menuitem"
                    disabled={busy}
                    className="block w-full px-3 py-2 text-left text-sm text-ink hover:bg-accentSoft hover:text-accent disabled:opacity-50"
                    onClick={() => {
                      setClearOpen(false);
                      act(() => api.bulk("clear_completed"), "Cleared completed");
                    }}
                  >
                    Clear completed
                  </button>
                  <button
                    type="button"
                    role="menuitem"
                    disabled={busy}
                    className="block w-full px-3 py-2 text-left text-sm text-failed hover:bg-rose-50 disabled:opacity-50"
                    onClick={() => {
                      setClearOpen(false);
                      if (window.confirm("Clear all tests? This cannot be undone.")) {
                        act(() => api.bulk("clear_all"), "All tests cleared");
                      }
                    }}
                  >
                    Clear all
                  </button>
                </div>
              ) : null}
            </div>
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

function IconBtn({
  children,
  onClick,
  disabled,
  label,
  tone = "default",
  wide = false,
  "aria-haspopup": ariaHaspopup,
  "aria-expanded": ariaExpanded,
}: {
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  label: string;
  tone?: "default" | "danger";
  wide?: boolean;
  "aria-haspopup"?: "menu";
  "aria-expanded"?: boolean;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      aria-label={label}
      title={label}
      aria-haspopup={ariaHaspopup}
      aria-expanded={ariaExpanded}
      className={`inline-flex h-10 items-center justify-center rounded-xl border disabled:opacity-50 ${
        wide ? "w-12" : "w-10"
      } ${
        tone === "danger"
          ? "border-rose-200 bg-rose-50 text-failed"
          : "border-line bg-canvas text-ink hover:bg-accentSoft hover:text-accent"
      }`}
    >
      {children}
    </button>
  );
}

function IconPlus() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 5v14M5 12h14"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}

function IconPlay() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M8 5.5v13l11-6.5-11-6.5z" />
    </svg>
  );
}

function IconPause() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <rect x="6" y="5" width="4" height="14" rx="1" />
      <rect x="14" y="5" width="4" height="14" rx="1" />
    </svg>
  );
}

function IconStop() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <rect x="6" y="6" width="12" height="12" rx="1.5" />
    </svg>
  );
}

function IconTrash() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 7h16M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2m2 0v12a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V7h12z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M10 11v6M14 11v6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function IconChevronDown() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M6 9l6 6 6-6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
