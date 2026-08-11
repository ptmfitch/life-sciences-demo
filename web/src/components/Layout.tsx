import { NavLink, Outlet } from "react-router-dom";
import type { ConnectionState } from "../lib/types";

const links = [
  { to: "/", label: "Monitor", end: true },
  { to: "/etl", label: "ETL" },
  { to: "/dashboards", label: "Dashboards" },
];

export function Layout({
  connection,
  toast,
}: {
  connection: ConnectionState;
  toast: string | null;
}) {
  const connColor =
    connection === "live"
      ? "bg-healthy"
      : connection === "reconnecting"
        ? "bg-attention"
        : "bg-failed";

  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-card/80 backdrop-blur sticky top-0 z-20">
        <div className="mx-auto max-w-[1440px] px-6 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-6">
            <div>
              <div className="text-xs uppercase tracking-[0.14em] text-muted">
                Synthetic demo
              </div>
              <h1 className="text-lg font-semibold text-ink">
                AstraLume BioTest Console
              </h1>
            </div>
            <nav className="flex items-center gap-1">
              {links.map((l) => (
                <NavLink
                  key={l.to}
                  to={l.to}
                  end={l.end}
                  className={({ isActive }) =>
                    `rounded-lg px-3 py-2 text-sm font-medium transition ${
                      isActive
                        ? "bg-accentSoft text-accent"
                        : "text-muted hover:text-ink hover:bg-canvas"
                    }`
                  }
                >
                  {l.label}
                </NavLink>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2 text-muted">
              <span className={`inline-block h-2 w-2 rounded-full ${connColor}`} />
              <span className="capitalize">{connection}</span>
            </div>
            <span
              className="rounded-full bg-accentSoft px-3 py-1 text-xs font-medium text-accent"
              title="Illustrative synthetic data only — not clinically or scientifically validated."
            >
              Illustrative only
            </span>
          </div>
        </div>
      </header>

      {toast && (
        <div className="fixed right-6 top-20 z-50 rounded-xl border border-line bg-card px-4 py-3 shadow-card text-sm">
          {toast}
        </div>
      )}

      <main className="mx-auto max-w-[1440px] px-6 py-6">
        <Outlet />
      </main>
    </div>
  );
}