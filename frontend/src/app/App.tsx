import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "../components/layout/AppShell";
import { AskPage } from "../pages/AskPage";
import { DesignSystemPage } from "../pages/DesignSystemPage";
import { MetricsPage } from "../pages/MetricsPage";
import { OpsPage } from "../pages/OpsPage";
import { OverviewPage } from "../pages/OverviewPage";
import { SyncPage } from "../pages/SyncPage";

export function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/sync" element={<SyncPage />} />
        <Route path="/ask" element={<AskPage />} />
        <Route path="/metrics" element={<MetricsPage />} />
        <Route path="/ops" element={<OpsPage />} />
        <Route path="/design-system" element={<DesignSystemPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}
