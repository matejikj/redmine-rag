import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { JobStatusBadge } from "../components/domain/JobStatusBadge";
import { PageHeader } from "../components/layout/PageHeader";
import { ErrorState } from "../components/states/ErrorState";
import { LoadingState } from "../components/states/LoadingState";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { DataTable } from "../components/ui/DataTable";
import { SelectField } from "../components/ui/SelectField";
import { TextField } from "../components/ui/TextField";
import {
  useHealthQuery,
  useOpsBackupMutation,
  useOpsEnvironmentQuery,
  useOpsMaintenanceMutation,
  useOpsRunsQuery
} from "../lib/api/hooks";
import type { HealthCheck, OpsRunRecord } from "../lib/api/types";
import { toUserMessage } from "../lib/utils/errors";

const CHECKLIST_KEY = "redmine-rag.ops.release-checklist.v1";
const CHECKLIST_ITEMS = [
  "Backend /healthz is stable and reports no hard failures.",
  "Sync -> Extract -> Ask -> Metrics journey validated in UI.",
  "Ops backup action executed and snapshot manifest verified.",
  "Ops maintenance action completed without errors.",
  "Eval regression gate status reviewed and accepted.",
  "Frontend /app bundle build validated for release."
] as const;

function parseChecklist(raw: string | null): boolean[] {
  if (!raw) {
    return CHECKLIST_ITEMS.map(() => false);
  }
  try {
    const parsed = JSON.parse(raw) as boolean[];
    return CHECKLIST_ITEMS.map((_, index) => Boolean(parsed[index]));
  } catch {
    return CHECKLIST_ITEMS.map(() => false);
  }
}

function parseLlmTelemetryDetail(detail: string | null): string {
  if (!detail) {
    return "Telemetry detail unavailable";
  }
  try {
    const payload = JSON.parse(detail) as {
      success_rate?: number;
      p95_latency_ms?: number | null;
      circuit?: { state?: string };
    };
    const successRate =
      typeof payload.success_rate === "number" ? `${(payload.success_rate * 100).toFixed(1)}%` : "-";
    const p95 =
      typeof payload.p95_latency_ms === "number" ? `${payload.p95_latency_ms} ms` : "-";
    const circuit = payload.circuit?.state ?? "unknown";
    return `success=${successRate}, p95=${p95}, circuit=${circuit}`;
  } catch {
    return detail;
  }
}

export function OpsPage() {
  const healthQuery = useHealthQuery();
  const environmentQuery = useOpsEnvironmentQuery();
  const runsQuery = useOpsRunsQuery();
  const backupMutation = useOpsBackupMutation();
  const maintenanceMutation = useOpsMaintenanceMutation();

  const [backupOutputDir, setBackupOutputDir] = useState("backups");
  const [checkStatusFilter, setCheckStatusFilter] = useState<"all" | "ok" | "warn" | "fail">("all");
  const [checklist, setChecklist] = useState<boolean[]>(CHECKLIST_ITEMS.map(() => false));

  useEffect(() => {
    const stored = window.localStorage.getItem(CHECKLIST_KEY);
    setChecklist(parseChecklist(stored));
  }, []);

  useEffect(() => {
    window.localStorage.setItem(CHECKLIST_KEY, JSON.stringify(checklist));
  }, [checklist]);

  const filteredChecks = useMemo(() => {
    const checks = healthQuery.data?.checks ?? [];
    if (checkStatusFilter === "all") {
      return checks;
    }
    return checks.filter((check) => check.status === checkStatusFilter);
  }, [healthQuery.data?.checks, checkStatusFilter]);

  const healthColumns = useMemo(
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
        render: (check: HealthCheck) =>
          check.name === "llm_telemetry"
            ? parseLlmTelemetryDetail(check.detail)
            : check.detail ?? "-"
      }
    ],
    []
  );

  const runColumns = useMemo(
    () => [
      {
        key: "action",
        header: "Action",
        render: (run: OpsRunRecord) => run.action
      },
      {
        key: "status",
        header: "Status",
        render: (run: OpsRunRecord) => <JobStatusBadge status={run.status === "success" ? "finished" : "failed"} />
      },
      {
        key: "started",
        header: "Started",
        render: (run: OpsRunRecord) => new Date(run.started_at).toLocaleString()
      },
      {
        key: "finished",
        header: "Finished",
        render: (run: OpsRunRecord) => new Date(run.finished_at).toLocaleString()
      },
      {
        key: "detail",
        header: "Detail",
        render: (run: OpsRunRecord) => run.detail
      }
    ],
    []
  );

  const refreshAll = () => {
    void healthQuery.refetch();
    void environmentQuery.refetch();
    void runsQuery.refetch();
  };

  const runBackup = () => {
    backupMutation.mutate(
      { output_dir: backupOutputDir.trim() ? backupOutputDir.trim() : null },
      {
        onSuccess: () => {
          void runsQuery.refetch();
        }
      }
    );
  };

  const runMaintenance = () => {
    maintenanceMutation.mutate(undefined, {
      onSuccess: () => {
        void runsQuery.refetch();
      }
    });
  };

  const checklistDone = checklist.filter(Boolean).length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Ops, Release, and Hardening"
        subtitle="Run backup and maintenance from UI, inspect environment/runtime checks, and complete release readiness without terminal-only steps."
        actions={
          <Button variant="secondary" onClick={refreshAll}>
            Refresh now
          </Button>
        }
      />

      {(healthQuery.isLoading || environmentQuery.isLoading || runsQuery.isLoading) ? (
        <LoadingState label="Loading ops dashboard" />
      ) : null}

      {healthQuery.isError ? (
        <ErrorState
          message={toUserMessage(healthQuery.error)}
          onRetry={() => {
            void healthQuery.refetch();
          }}
        />
      ) : null}
      {environmentQuery.isError ? (
        <ErrorState
          message={toUserMessage(environmentQuery.error)}
          onRetry={() => {
            void environmentQuery.refetch();
          }}
        />
      ) : null}
      {runsQuery.isError ? (
        <ErrorState
          message={toUserMessage(runsQuery.error)}
          onRetry={() => {
            void runsQuery.refetch();
          }}
        />
      ) : null}

      {environmentQuery.data ? (
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Card title="Application" description="Version and environment">
            <p className="text-sm text-[var(--ink-1)]">{environmentQuery.data.app}</p>
            <p className="mt-1 text-xs text-[var(--ink-2)]">
              v{environmentQuery.data.version} · env={environmentQuery.data.app_env}
            </p>
          </Card>
          <Card title="LLM Runtime" description="Provider and model">
            <p className="text-sm text-[var(--ink-1)]">
              {environmentQuery.data.llm_provider}/{environmentQuery.data.llm_model}
            </p>
            <p className="mt-1 text-xs text-[var(--ink-2)]">
              extract_enabled={String(environmentQuery.data.llm_extract_enabled)}
            </p>
          </Card>
          <Card title="Redmine Endpoint" description="Configured API base URL">
            <p className="text-sm text-[var(--ink-1)]">{environmentQuery.data.redmine_base_url}</p>
            <p className="mt-1 text-xs text-[var(--ink-2)]">
              allowlist={environmentQuery.data.redmine_allowed_hosts.join(", ") || "-"}
            </p>
          </Card>
          <Card title="Health Snapshot" description="From /healthz">
            <p className="text-2xl font-semibold text-[var(--ink-1)]">{healthQuery.data?.status ?? "-"}</p>
            <p className="mt-1 text-xs text-[var(--ink-2)]">
              {healthQuery.data ? new Date(healthQuery.data.utc_time).toLocaleString() : "-"}
            </p>
          </Card>
        </section>
      ) : null}

      <Card
        title="Operations Controls"
        description="Backup and maintenance actions with immediate feedback and run logging."
      >
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto_auto]">
          <TextField
            label="Backup output directory"
            name="backupOutputDir"
            value={backupOutputDir}
            onChange={(event) => setBackupOutputDir(event.target.value)}
            hint="Directory where snapshot-<timestamp> folders are created."
          />
          <div className="self-end">
            <Button onClick={runBackup} disabled={backupMutation.isPending}>
              {backupMutation.isPending ? "Running backup…" : "Run backup"}
            </Button>
          </div>
          <div className="self-end">
            <Button variant="secondary" onClick={runMaintenance} disabled={maintenanceMutation.isPending}>
              {maintenanceMutation.isPending ? "Running maintenance…" : "Run maintenance"}
            </Button>
          </div>
        </div>

        {backupMutation.isError ? (
          <p className="mt-3 text-sm text-[var(--danger-ink)]">{toUserMessage(backupMutation.error)}</p>
        ) : null}
        {maintenanceMutation.isError ? (
          <p className="mt-3 text-sm text-[var(--danger-ink)]">
            {toUserMessage(maintenanceMutation.error)}
          </p>
        ) : null}

        {backupMutation.data ? (
          <p className="mt-3 rounded-xl bg-[var(--success-soft)] px-3 py-2 text-sm text-[#1d5f1f]">
            Backup run {backupMutation.data.run.status}: {backupMutation.data.run.detail}
          </p>
        ) : null}
        {maintenanceMutation.data ? (
          <p className="mt-3 rounded-xl bg-[var(--surface-2)] px-3 py-2 text-sm text-[var(--ink-1)]">
            Maintenance run {maintenanceMutation.data.run.status}: {maintenanceMutation.data.run.detail}
          </p>
        ) : null}
      </Card>

      <Card
        title="Operations Run History"
        description="Recent backup/maintenance runs captured by backend service."
      >
        {runsQuery.data && runsQuery.data.items.length > 0 ? (
          <DataTable columns={runColumns} items={runsQuery.data.items} rowKey={(run) => run.id} />
        ) : (
          <p className="text-sm text-[var(--ink-2)]">No ops runs recorded yet.</p>
        )}
      </Card>

      <Card
        title="Health Checks"
        description="Filter checks by severity to focus incident response quickly."
      >
        <div className="mb-4 grid gap-3 md:grid-cols-[220px_minmax(0,1fr)]">
          <SelectField
            label="Status filter"
            name="checkStatusFilter"
            value={checkStatusFilter}
            onChange={(event) => setCheckStatusFilter(event.target.value as "all" | "ok" | "warn" | "fail")}
            options={[
              { label: "All", value: "all" },
              { label: "OK", value: "ok" },
              { label: "Warn", value: "warn" },
              { label: "Fail", value: "fail" }
            ]}
          />
          <p className="self-end text-xs text-[var(--ink-2)]">
            Workflow links: <Link to="/sync" className="underline">sync</Link> ·{" "}
            <Link to="/ask" className="underline">ask</Link> ·{" "}
            <Link to="/metrics" className="underline">metrics</Link>
          </p>
        </div>
        <DataTable
          columns={healthColumns}
          items={filteredChecks}
          rowKey={(check) => `${check.name}-${check.status}`}
        />
      </Card>

      <Card
        title="Release Readiness Checklist"
        description="UI and API cutover checklist for go-live rehearsal."
      >
        <p className="mb-3 text-sm text-[var(--ink-1)]">
          Completed {checklistDone}/{CHECKLIST_ITEMS.length}
        </p>
        <ul className="space-y-2">
          {CHECKLIST_ITEMS.map((item, index) => (
            <li key={item}>
              <label className="inline-flex items-start gap-2 text-sm text-[var(--ink-1)]">
                <input
                  type="checkbox"
                  checked={checklist[index] ?? false}
                  onChange={(event) => {
                    setChecklist((previous) => {
                      const next = [...previous];
                      next[index] = event.target.checked;
                      return next;
                    });
                  }}
                />
                <span>{item}</span>
              </label>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
