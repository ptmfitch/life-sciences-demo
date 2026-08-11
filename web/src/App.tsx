import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { useLiveRuns } from "./lib/sse";
import { DashboardsPage } from "./pages/Dashboards";
import { EtlPage } from "./pages/Etl";
import { MonitorPage } from "./pages/Monitor";

export default function App() {
  const { runs, connection, toast, showToast } = useLiveRuns();

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout connection={connection} toast={toast} />}>
          <Route path="/" element={<MonitorPage runs={runs} showToast={showToast} />} />
          <Route path="/etl" element={<EtlPage showToast={showToast} />} />
          <Route path="/dashboards" element={<DashboardsPage showToast={showToast} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}