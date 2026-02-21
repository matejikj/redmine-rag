import { useMemo } from "react";

import { JobStatusBadge } from "../components/domain/JobStatusBadge";
import { PageHeader } from "../components/layout/PageHeader";
import { ErrorState } from "../components/states/ErrorState";
import { LoadingState } from "../components/states/LoadingState";
import { Card } from "../components/ui/Card";
import { DataTable } from "../components/ui/DataTable";
import { useHealthQuery } from "../lib/api/hooks";
import type { HealthCheck } from "../lib/api/types";
import { toUserMessage } from "../lib/utils/errors";

export function OpsPage() {
  const healthQuery = useHealthQuery();

  const columns = useMemo(
    () => [
      { key: "name", header: "Check", render: (check: HealthCheck) => check.name },
      {
        key: "status",
        header: "Status",
        render: (check: HealthCheck) => <JobStatusBadge status={check.status} />
      },
      {
        key: "latency",
        header: "Latency",
        render: (check: HealthCheck) => (check.latency_ms ? `${check.latency_ms} ms` : "-")
      },
      {
        key: "detail",
        header: "Detail",
        render: (check: HealthCheck) => check.detail ?? "-"
      }
    ],
    []
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Ops Diagnostics"
        subtitle="Health checks, runtime readiness and release-facing diagnostics in a terminal-free view."
      />

      {healthQuery.isLoading ? <LoadingState label="Loading health checks" /> : null}
      {healthQuery.isError ? (
        <ErrorState
          message={toUserMessage(healthQuery.error)}
          onRetry={() => {
            void healthQuery.refetch();
          }}
        />
      ) : null}

      {healthQuery.data ? (
        <>
          <section className="grid gap-4 md:grid-cols-3">
            <Card title="App" description="Service identity and version">
              <p className="text-sm text-[var(--ink-1)]">{healthQuery.data.app}</p>
              <p className="mt-1 text-xs text-[var(--ink-2)]">Version {healthQuery.data.version}</p>
            </Card>
            <Card title="Overall status" description="Derived from all health checks">
              <p className="text-2xl font-semibold text-[var(--ink-1)]">{healthQuery.data.status}</p>
            </Card>
            <Card title="Reported at" description="UTC timestamp from backend">
              <p className="text-sm text-[var(--ink-1)]">{healthQuery.data.utc_time}</p>
            </Card>
          </section>

          <DataTable
            columns={columns}
            items={healthQuery.data.checks}
            rowKey={(check) => `${check.name}-${check.status}`}
          />
        </>
      ) : null}
    </div>
  );
}
