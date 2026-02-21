import { useMemo, useState } from "react";

import { JobStatusBadge } from "../components/domain/JobStatusBadge";
import { PageHeader } from "../components/layout/PageHeader";
import { EmptyState } from "../components/states/EmptyState";
import { ErrorState } from "../components/states/ErrorState";
import { LoadingState } from "../components/states/LoadingState";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { DataTable } from "../components/ui/DataTable";
import { SelectField } from "../components/ui/SelectField";
import { TextField } from "../components/ui/TextField";
import { useSyncJobsQuery, useTriggerSyncMutation } from "../lib/api/hooks";
import type { SyncJobResponse } from "../lib/api/types";
import { toUserMessage } from "../lib/utils/errors";

export function SyncPage() {
  const [projectScope, setProjectScope] = useState("1");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const syncMutation = useTriggerSyncMutation();
  const jobsQuery = useSyncJobsQuery(statusFilter === "all" ? null : statusFilter);

  const rows = jobsQuery.data?.items ?? [];
  const columns = useMemo(
    () => [
      {
        key: "id",
        header: "Job",
        render: (item: SyncJobResponse) => <code className="text-xs">{item.id.slice(0, 10)}</code>
      },
      {
        key: "status",
        header: "Status",
        render: (item: SyncJobResponse) => <JobStatusBadge status={item.status} />
      },
      {
        key: "started",
        header: "Started",
        render: (item: SyncJobResponse) => item.started_at ?? "-"
      },
      {
        key: "finished",
        header: "Finished",
        render: (item: SyncJobResponse) => item.finished_at ?? "-"
      },
      {
        key: "error",
        header: "Error",
        render: (item: SyncJobResponse) => item.error_message ?? "-"
      }
    ],
    []
  );

  const onTriggerSync = () => {
    const parsed = projectScope
      .split(",")
      .map((value) => Number.parseInt(value.trim(), 10))
      .filter((value) => Number.isFinite(value) && value > 0);

    syncMutation.mutate(
      { project_ids: parsed.length > 0 ? parsed : null },
      {
        onSuccess: () => {
          void jobsQuery.refetch();
        }
      }
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Sync and Ingestion"
        subtitle="Trigger incremental Redmine sync jobs and monitor queue/running/finished/failed transitions in one table."
      />

      <Card title="Trigger Sync" description="Use comma-separated project IDs, or leave empty for configured defaults.">
        <form
          className="grid gap-4 md:grid-cols-[minmax(0,1fr)_220px_auto] md:items-end"
          onSubmit={(event) => {
            event.preventDefault();
            onTriggerSync();
          }}
        >
          <TextField
            label="Project scope"
            name="projectScope"
            value={projectScope}
            onChange={(event) => setProjectScope(event.target.value)}
            hint="Example: 1,2,9"
          />
          <SelectField
            label="Status filter"
            name="status"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            options={[
              { label: "All statuses", value: "all" },
              { label: "Queued", value: "queued" },
              { label: "Running", value: "running" },
              { label: "Finished", value: "finished" },
              { label: "Failed", value: "failed" }
            ]}
          />
          <Button type="submit" disabled={syncMutation.isPending}>
            {syncMutation.isPending ? "Starting…" : "Start sync"}
          </Button>
        </form>

        {syncMutation.isError ? (
          <p className="mt-3 text-sm text-[var(--danger-ink)]">{toUserMessage(syncMutation.error)}</p>
        ) : null}

        {syncMutation.data ? (
          <p className="mt-3 rounded-xl bg-[var(--success-soft)] px-3 py-2 text-sm text-[#1d5f1f]">
            Job accepted: <code>{syncMutation.data.job_id}</code>
          </p>
        ) : null}
      </Card>

      {jobsQuery.isLoading ? <LoadingState label="Loading sync jobs" /> : null}

      {jobsQuery.isError ? (
        <ErrorState
          message={toUserMessage(jobsQuery.error)}
          onRetry={() => {
            void jobsQuery.refetch();
          }}
        />
      ) : null}

      {jobsQuery.data && rows.length === 0 ? (
        <EmptyState
          title="No jobs yet"
          description="Trigger your first sync run to populate ingestion history."
        />
      ) : null}

      {rows.length > 0 ? <DataTable columns={columns} items={rows} rowKey={(item) => item.id} /> : null}
    </div>
  );
}
