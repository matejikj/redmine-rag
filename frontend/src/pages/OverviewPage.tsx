import { Link } from "react-router-dom";

import { PageHeader } from "../components/layout/PageHeader";
import { ErrorState } from "../components/states/ErrorState";
import { LoadingState } from "../components/states/LoadingState";
import { Card } from "../components/ui/Card";
import { useHealthQuery } from "../lib/api/hooks";
import { toUserMessage } from "../lib/utils/errors";

const workflows = [
  {
    title: "Sync and ingestion",
    description: "Start incremental sync jobs and inspect their status transitions.",
    to: "/sync"
  },
  {
    title: "Ask with grounding",
    description: "Submit project questions and validate evidence with citations.",
    to: "/ask"
  },
  {
    title: "Metrics and extraction",
    description: "Review extracted issue quality and per-project trends.",
    to: "/metrics"
  },
  {
    title: "Ops diagnostics",
    description: "Monitor runtime health and identify failure modes quickly.",
    to: "/ops"
  }
];

export function OverviewPage() {
  const healthQuery = useHealthQuery();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Platform Control Plane"
        subtitle="Desktop and mobile-friendly workspace to run sync, query grounded answers, and monitor operational health."
      />

      {healthQuery.isLoading ? <LoadingState label="Loading runtime health" /> : null}

      {healthQuery.isError ? (
        <ErrorState
          title="Health endpoint unavailable"
          message={toUserMessage(healthQuery.error)}
          onRetry={() => {
            void healthQuery.refetch();
          }}
        />
      ) : null}

      {healthQuery.data ? (
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card title="API Status" description="Current /healthz status">
            <p className="text-2xl font-semibold text-[var(--ink-1)]">{healthQuery.data.status}</p>
          </Card>
          <Card title="Queued Jobs" description="Sync jobs waiting for processing">
            <p className="text-2xl font-semibold text-[var(--ink-1)]">{healthQuery.data.sync_jobs.queued}</p>
          </Card>
          <Card title="Running Jobs" description="Jobs currently in progress">
            <p className="text-2xl font-semibold text-[var(--ink-1)]">{healthQuery.data.sync_jobs.running}</p>
          </Card>
          <Card title="Failed Jobs" description="Jobs requiring operator attention">
            <p className="text-2xl font-semibold text-[var(--danger-ink)]">{healthQuery.data.sync_jobs.failed}</p>
          </Card>
        </section>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2">
        {workflows.map((workflow) => (
          <Card key={workflow.to} title={workflow.title} description={workflow.description}>
            <Link
              to={workflow.to}
              className="text-sm font-semibold text-[var(--brand-strong)] underline decoration-[var(--brand)] decoration-2 underline-offset-2"
            >
              Open workspace
            </Link>
          </Card>
        ))}
      </section>
    </div>
  );
}
