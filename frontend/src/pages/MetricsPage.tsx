import { PageHeader } from "../components/layout/PageHeader";
import { EmptyState } from "../components/states/EmptyState";
import { Card } from "../components/ui/Card";

export function MetricsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Metrics and Extraction"
        subtitle="Foundation route for metrics charts, extraction controls, and eval gate widgets in following tasks."
      />

      <Card title="Data refresh pattern" description="UI foundation for deterministic data windows.">
        <p className="text-sm text-[var(--ink-1)]">
          This page will load `/v1/metrics/summary` and extraction diagnostics in Task 19. The shared
          loading/empty/error states are already available for those flows.
        </p>
      </Card>

      <EmptyState
        title="No dashboard widgets yet"
        description="Task 19 will add metric charts, extraction counters and regression health cards here."
      />
    </div>
  );
}
