import { useEffect, useMemo, useState } from "react";

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
import { useSyncJobQuery, useSyncJobsQuery, useTriggerSyncMutation } from "../lib/api/hooks";
import { SYNC_MODULES, type SyncJobResponse, type SyncModule } from "../lib/api/types";
import { toUserMessage } from "../lib/utils/errors";
import {
  buildRetryPayload,
  extractModulesFromPayload,
  extractSyncSummary,
  formatDuration,
  getFailureRecommendations,
  parseProjectScope
} from "./syncUtils";

const STORAGE_KEY = "redmine-rag.sync.control-center.v1";

interface PersistedState {
  projectScope: string;
  statusFilter: string;
  selectedModules: string[];
  selectedJobId: string | null;
}

function loadPersistedState(): PersistedState {
  const fallback: PersistedState = {
    projectScope: "1",
    statusFilter: "all",
    selectedModules: [...SYNC_MODULES],
    selectedJobId: null
  };
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return fallback;
  }
  try {
    const parsed = JSON.parse(raw) as Partial<PersistedState>;
    return {
      projectScope: parsed.projectScope ?? fallback.projectScope,
      statusFilter: parsed.statusFilter ?? fallback.statusFilter,
      selectedModules:
        Array.isArray(parsed.selectedModules) && parsed.selectedModules.length > 0
          ? parsed.selectedModules
          : fallback.selectedModules,
      selectedJobId: parsed.selectedJobId ?? fallback.selectedJobId
    };
  } catch {
    return fallback;
  }
}

function savePersistedState(state: PersistedState): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export function SyncPage() {
  const [projectScope, setProjectScope] = useState("1");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedModules, setSelectedModules] = useState<string[]>([...SYNC_MODULES]);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  const syncMutation = useTriggerSyncMutation();
  const jobsQuery = useSyncJobsQuery(statusFilter === "all" ? null : statusFilter);
  const detailQuery = useSyncJobQuery(selectedJobId);

  useEffect(() => {
    const restored = loadPersistedState();
    setProjectScope(restored.projectScope);
    setStatusFilter(restored.statusFilter);
    setSelectedModules(restored.selectedModules);
    setSelectedJobId(restored.selectedJobId);
  }, []);

  useEffect(() => {
    savePersistedState({
      projectScope,
      statusFilter,
      selectedModules,
      selectedJobId
    });
  }, [projectScope, statusFilter, selectedModules, selectedJobId]);

  const rows = jobsQuery.data?.items ?? [];

  useEffect(() => {
    if (!selectedJobId && rows.length > 0) {
      setSelectedJobId(rows[0].id);
    }
    if (selectedJobId && rows.length > 0 && !rows.some((row) => row.id === selectedJobId)) {
      setSelectedJobId(rows[0].id);
    }
  }, [rows, selectedJobId]);

  const columns = useMemo(
    () => [
      {
        key: "id",
        header: "Job",
        render: (item: SyncJobResponse) => <code className="text-xs">{item.id.slice(0, 12)}</code>
      },
      {
        key: "status",
        header: "Status",
        render: (item: SyncJobResponse) => <JobStatusBadge status={item.status} />
      },
      {
        key: "projects",
        header: "Projects",
        render: (item: SyncJobResponse) => {
          const projects = Array.isArray(item.payload.project_ids) ? item.payload.project_ids : [];
          return projects.length > 0 ? projects.join(", ") : "default";
        }
      },
      {
        key: "modules",
        header: "Modules",
        render: (item: SyncJobResponse) => {
          const modules = extractModulesFromPayload(item.payload);
          return modules.length > 0 ? modules.join(", ") : "configured defaults";
        }
      },
      {
        key: "duration",
        header: "Duration",
        render: (item: SyncJobResponse) => formatDuration(item.started_at, item.finished_at)
      },
      {
        key: "updated",
        header: "Updated",
        render: (item: SyncJobResponse) => item.updated_at
      }
    ],
    []
  );

  const selectedJob = detailQuery.data ?? rows.find((row) => row.id === selectedJobId) ?? null;
  const selectedSummary = selectedJob ? extractSyncSummary(selectedJob.payload) : null;
  const failureRecommendations = selectedJob ? getFailureRecommendations(selectedJob) : [];

  const onToggleModule = (module: SyncModule, checked: boolean) => {
    setSelectedModules((previous) => {
      if (checked) {
        if (previous.includes(module)) {
          return previous;
        }
        return [...previous, module];
      }
      if (previous.length <= 1) {
        return previous;
      }
      return previous.filter((item) => item !== module);
    });
  };

  const onTriggerSync = () => {
    const projectIds = parseProjectScope(projectScope);
    syncMutation.mutate(
      {
        project_ids: projectIds.length > 0 ? projectIds : null,
        modules: selectedModules.length > 0 ? selectedModules : null
      },
      {
        onSuccess: async () => {
          const refreshed = await jobsQuery.refetch();
          const first = refreshed.data?.items?.[0];
          if (first) {
            setSelectedJobId(first.id);
          }
        }
      }
    );
  };

  const retrySelectedJob = () => {
    if (!selectedJob) {
      return;
    }
    syncMutation.mutate(buildRetryPayload(selectedJob), {
      onSuccess: async () => {
        const refreshed = await jobsQuery.refetch();
        const first = refreshed.data?.items?.[0];
        if (first) {
          setSelectedJobId(first.id);
        }
      }
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Sync and Ingestion Control Center"
        subtitle="Trigger scoped sync runs, monitor queue/running/failed states in real-time, inspect ingestion summaries, and retry failed jobs with one click."
        actions={
          <Button
            variant="secondary"
            onClick={() => {
              void jobsQuery.refetch();
              if (selectedJobId) {
                void detailQuery.refetch();
              }
            }}
          >
            Refresh now
          </Button>
        }
      />

      <Card
        title="Trigger Sync Job"
        description="Define project scope and module set. Configuration persists across refreshes."
      >
        <form
          className="space-y-4"
          onSubmit={(event) => {
            event.preventDefault();
            onTriggerSync();
          }}
        >
          <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_220px]">
            <TextField
              label="Project scope"
              name="projectScope"
              value={projectScope}
              onChange={(event) => setProjectScope(event.target.value)}
              hint="Comma-separated Redmine project IDs. Empty = configured defaults."
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
          </div>

          <fieldset className="space-y-2">
            <legend className="text-sm font-medium text-[var(--ink-1)]">Module toggles</legend>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {SYNC_MODULES.map((module) => (
                <label
                  key={module}
                  className="flex items-center gap-2 rounded-xl border border-[var(--border)] bg-[var(--surface-1)] px-3 py-2 text-sm text-[var(--ink-1)]"
                >
                  <input
                    type="checkbox"
                    checked={selectedModules.includes(module)}
                    onChange={(event) => onToggleModule(module, event.target.checked)}
                  />
                  <span>{module}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <div className="flex flex-wrap gap-2">
            <Button type="submit" disabled={syncMutation.isPending}>
              {syncMutation.isPending ? "Starting…" : "Start sync"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={retrySelectedJob}
              disabled={!selectedJob || syncMutation.isPending}
            >
              Retry selected job
            </Button>
          </div>
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

      {rows.length > 0 ? (
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]">
          <Card title="Live Job List" description="Select a row to inspect full detail and ingestion summary.">
            <DataTable
              columns={columns}
              items={rows}
              rowKey={(item) => item.id}
              onRowClick={(item) => setSelectedJobId(item.id)}
              selectedRowKey={selectedJobId}
            />
          </Card>

          <Card
            title="Job Detail"
            description={selectedJobId ? `Selected job: ${selectedJobId}` : "Select a job from the list"}
          >
            {detailQuery.isLoading && selectedJobId ? <LoadingState label="Loading job detail" /> : null}
            {detailQuery.isError ? (
              <ErrorState
                message={toUserMessage(detailQuery.error)}
                onRetry={() => {
                  void detailQuery.refetch();
                }}
              />
            ) : null}

            {selectedJob ? (
              <div className="space-y-4">
                <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-3 text-sm">
                  <p>
                    <strong>Status:</strong> <JobStatusBadge status={selectedJob.status} />
                  </p>
                  <p>
                    <strong>Started:</strong> {selectedJob.started_at ?? "-"}
                  </p>
                  <p>
                    <strong>Finished:</strong> {selectedJob.finished_at ?? "-"}
                  </p>
                  <p>
                    <strong>Duration:</strong> {formatDuration(selectedJob.started_at, selectedJob.finished_at)}
                  </p>
                  <p>
                    <strong>Projects:</strong>{" "}
                    {Array.isArray(selectedJob.payload.project_ids)
                      ? selectedJob.payload.project_ids.join(", ") || "default"
                      : "default"}
                  </p>
                  <p>
                    <strong>Modules:</strong>{" "}
                    {extractModulesFromPayload(selectedJob.payload).join(", ") || "configured defaults"}
                  </p>
                </div>

                {selectedSummary ? (
                  <>
                    <div className="grid gap-3 md:grid-cols-2">
                      <Card title="Entity summary" description="Core ingestion entities synced in this run.">
                        <ul className="space-y-1 text-sm text-[var(--ink-1)]">
                          {selectedSummary.entities.map((row) => (
                            <li key={row.label} className="flex items-center justify-between">
                              <span>{row.label}</span>
                              <strong>{row.value}</strong>
                            </li>
                          ))}
                        </ul>
                      </Card>

                      <Card title="Chunk/vector summary" description="Indexing impact for this run.">
                        <ul className="space-y-1 text-sm text-[var(--ink-1)]">
                          {selectedSummary.indexing.map((row) => (
                            <li key={row.label} className="flex items-center justify-between">
                              <span>{row.label}</span>
                              <strong>{row.value}</strong>
                            </li>
                          ))}
                        </ul>
                      </Card>
                    </div>

                    <Card title="Modules" description="Enabled and skipped module details.">
                      <p className="text-sm text-[var(--ink-1)]">
                        Enabled: <strong>{selectedSummary.modulesEnabled.join(", ") || "-"}</strong>
                      </p>
                      {selectedSummary.modulesSkipped.length > 0 ? (
                        <ul className="mt-2 space-y-1 text-sm text-[var(--ink-1)]">
                          {selectedSummary.modulesSkipped.map((item, index) => (
                            <li key={`${item.module}-${item.reason}-${index}`}>
                              <strong>{item.module}</strong>: {item.reason}
                              {item.status_code ? ` (status=${item.status_code})` : ""}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="mt-2 text-sm text-[var(--ink-2)]">No skipped modules reported.</p>
                      )}
                    </Card>
                  </>
                ) : null}

                {selectedJob.status === "failed" ? (
                  <Card title="Failure diagnostics" description="Recommended next actions for operators.">
                    <p className="text-sm text-[var(--danger-ink)]">
                      <strong>Error:</strong> {selectedJob.error_message ?? "Unknown failure"}
                    </p>
                    <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-[var(--ink-1)]">
                      {failureRecommendations.map((recommendation) => (
                        <li key={recommendation}>{recommendation}</li>
                      ))}
                    </ol>
                  </Card>
                ) : null}
              </div>
            ) : (
              <EmptyState
                title="No selected job"
                description="Select a job row to inspect payload summary and diagnostics."
              />
            )}
          </Card>
        </div>
      ) : null}
    </div>
  );
}
