import type { AcceptanceReport, AuditEvent, SpecDisposition, SpecResult } from "../lib/types";
import { specResultClass } from "../lib/specResult";

function fmt1(value: number): string {
  return value.toFixed(1);
}

function ResultPill({ result }: { result: SpecResult }) {
  return (
    <span
      className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-medium ${specResultClass(result)}`}
    >
      {result}
    </span>
  );
}

function SpecimenTable({ rows }: { rows: SpecDisposition[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="text-xs uppercase text-muted">
          <tr>
            <th className="py-2 pr-3 text-left">Standard</th>
            <th className="py-2 pr-3 text-left">Activity</th>
            <th className="py-2 pr-3 text-left">Temp °C</th>
            <th className="py-2 pr-3 text-left">Activity result</th>
            <th className="py-2 pr-3 text-left">Temperature result</th>
            <th className="py-2 text-left">Overall</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label} className="border-t border-line">
              <td className="py-2 pr-3 font-mono">{row.label}</td>
              <td className="py-2 pr-3 font-mono">{fmt1(row.reported_activity)}</td>
              <td className="py-2 pr-3 font-mono">{fmt1(row.temperature_c)}</td>
              <td className="py-2 pr-3">
                <ResultPill result={row.activity_result} />
              </td>
              <td className="py-2 pr-3">
                <ResultPill result={row.temperature_result} />
              </td>
              <td className="py-2">
                <ResultPill result={row.overall} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatWhen(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export function AcceptancePanel({
  report,
  audit,
  busy,
  onRecalculate,
}: {
  report: AcceptanceReport | null;
  audit: AuditEvent[];
  busy: boolean;
  onRecalculate: () => void;
}) {
  return (
    <section
      id="specimen-acceptance"
      className="rounded-2xl border border-line bg-card p-5 shadow-card"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">Specimen acceptance</h2>
          <p className="mt-1 max-w-3xl text-sm text-muted">
            Reference standards use the same disposition as loaded assay averages and
            live monitor readings. Separate from the operational run labels (normal /
            attention).
          </p>
        </div>
        <button
          type="button"
          onClick={onRecalculate}
          disabled={busy || !report}
          className="rounded-xl bg-accent px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          Recalculate dispositions
        </button>
      </div>

      {!report ? (
        <p className="mt-4 text-sm text-muted">Loading acceptance results…</p>
      ) : (
        <>
          <div className="mt-3 rounded-xl bg-accentSoft px-3 py-2 text-xs text-accent">
            {report.activity_rule} {report.temperature_rule}
          </div>
          <p className="mt-2 text-xs text-muted">{report.disclaimer}</p>

          <h3 className="mb-2 mt-4 text-sm font-semibold">Reference standards</h3>
          <SpecimenTable rows={report.reference_specimens} />

          <h3 className="mb-2 mt-5 text-sm font-semibold">Loaded assay endpoints</h3>
          {report.loaded_runs.length === 0 ? (
            <p className="text-sm text-muted">
              No loaded telemetry yet. The standards above still disposition with the
              same calculation.
            </p>
          ) : (
            <SpecimenTable rows={report.loaded_runs} />
          )}
        </>
      )}

      <h3 className="mb-2 mt-5 text-sm font-semibold">Audit trail</h3>
      <p className="mb-2 text-xs text-muted">
        Append-only record of ETL loads and acceptance recalculations (who, what,
        when, why). Recalculate writes one event. Illustrative only.
      </p>
      {audit.length === 0 ? (
        <p className="text-sm text-muted">
          No audit events yet. Recalculate dispositions or load a CSV.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="text-xs uppercase text-muted">
              <tr>
                <th className="py-2 pr-3 text-left">When</th>
                <th className="py-2 pr-3 text-left">Who</th>
                <th className="py-2 pr-3 text-left">What</th>
                <th className="py-2 text-left">Why</th>
              </tr>
            </thead>
            <tbody>
              {audit.map((event) => (
                <tr key={event.id} className="border-t border-line">
                  <td className="py-2 pr-3 whitespace-nowrap text-xs">
                    {formatWhen(event.recorded_at)}
                  </td>
                  <td className="py-2 pr-3 font-mono text-xs">{event.actor}</td>
                  <td className="py-2 pr-3 font-mono text-xs">{event.action}</td>
                  <td className="py-2 text-xs">{event.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
