import { useCallback, useEffect, useRef, useState } from "react";
import type { ConnectionState, Run, TelemetryReading } from "./types";

const STREAM_URL = "/api/stream";

function mergeRun(prev: Run | undefined, patch: Partial<Run> & { id: string }): Run {
  const base = prev ?? ({
    id: patch.id,
    test_name: "",
    device_id: "",
    device_name: "AstraLume BioTest Station",
    rack_id: "",
    assay_run_id: "",
    compound_code: "",
    well_count: 24,
    status: "pending",
    seed: 0,
    tick_index: 0,
    row_count: 0,
    file_count: 0,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  } as Run);
  return { ...base, ...patch };
}

export function useLiveRuns() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [connection, setConnection] = useState<ConnectionState>("reconnecting");
  const [toast, setToast] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);
  const runsRef = useRef<Run[]>([]);

  useEffect(() => {
    runsRef.current = runs;
  }, [runs]);

  const showToast = useCallback((msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast(null), 4000);
  }, []);

  useEffect(() => {
    let closed = false;

    const connect = () => {
      if (closed) return;
      setConnection("reconnecting");
      const es = new EventSource(STREAM_URL);
      esRef.current = es;

      es.addEventListener("snapshot", (ev) => {
        try {
          const data = JSON.parse(ev.data) as { runs: Run[] };
          setRuns(data.runs || []);
          setConnection("live");
        } catch {
          /* ignore malformed */
        }
      });

      es.addEventListener("run_state", (ev) => {
        try {
          const patch = JSON.parse(ev.data) as Partial<Run> & { id: string; status?: string };
          if (patch.status === "cleared") {
            setRuns((prev) => prev.filter((r) => r.id !== patch.id));
            return;
          }
          setRuns((prev) => {
            const idx = prev.findIndex((r) => r.id === patch.id);
            if (idx === -1) {
              // Full object preferred; otherwise keep list and wait for refresh
              if (patch.test_name) return [mergeRun(undefined, patch), ...prev];
              return prev;
            }
            const next = [...prev];
            next[idx] = mergeRun(next[idx], patch);
            return next;
          });
        } catch {
          /* ignore */
        }
      });

      es.addEventListener("telemetry", (ev) => {
        try {
          const data = JSON.parse(ev.data) as {
            run_id: string;
            reading: TelemetryReading;
            tick_index: number;
          };
          setRuns((prev) =>
            prev.map((r) => {
              if (r.id !== data.run_id) return r;
              const spark = [...(r.sparkline || [])];
              if (data.reading.activity_index != null) {
                spark.push(data.reading.activity_index);
                if (spark.length > 60) spark.shift();
              }
              return {
                ...r,
                tick_index: data.tick_index + 1,
                elapsed_seconds: data.tick_index + 1,
                last_reading_at: data.reading.event_timestamp,
                latest: data.reading,
                wells: data.reading.wells || r.wells,
                sparkline: spark,
                row_count: (r.row_count || 0) + 1,
                _pulse: Date.now(),
              } as Run & { _pulse?: number };
            })
          );
        } catch {
          /* ignore */
        }
      });

      es.addEventListener("heartbeat", () => setConnection("live"));

      es.onopen = () => setConnection("live");
      es.onerror = () => {
        setConnection("reconnecting");
        es.close();
        window.setTimeout(connect, 1500);
      };
    };

    connect();
    return () => {
      closed = true;
      esRef.current?.close();
    };
  }, []);

  return { runs, setRuns, connection, toast, showToast };
}