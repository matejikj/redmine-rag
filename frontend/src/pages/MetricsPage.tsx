import { useMemo, useState } from "react";

import { PageHeader } from "../components/layout/PageHeader";
import { EmptyState } from "../components/states/EmptyState";
import { ErrorState } from "../components/states/ErrorState";
import { LoadingState } from "../components/states/LoadingState";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { DataTable } from "../components/ui/DataTable";
import { TextField } from "../components/ui/TextField";
import {
  useEvalArtifactsQuery,
  useExtractMutation,
  useMetricsSummaryQuery
} from "../lib/api/hooks";
import type { EvalComparisonRow, MetricsSummaryByProject } from "../lib/api/types";
import { toUserMessage } from "../lib/utils/errors";
import {
  buildMetricsExportPayload,
  formatDurationSeconds,
  formatPercent,
  metricLabel,
  parseCsvIds,
  parseExtractionCounters,
  parseExtractionIssueIds
} from "./metricsUtils";

function downloadJson(filename: string, payload: unknown): void {
  const json = JSON.stringify(payload, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

interface ExtractionRunSummary {
  requestedIssueIds: number[] | null;
  processedIssues: number;
  detail: string;
  finishedAt: string;
  counters: {
    success: number;
    failed: number;
    skipped: number;
    retries: number;
  } | null;
}

export function MetricsPage() {
  const [projectIds, setProjectIds] = useState("1");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [extractIssueIds, setExtractIssueIds] = useState("");
  const [lastManualRefreshAt, setLastManualRefreshAt] = useState<string | null>(null);
  const [latestExtraction, setLatestExtraction] = useState<ExtractionRunSummary | null>(null);

  const parsedProjectIds = useMemo(() => parseCsvIds(projectIds), [projectIds]);
  const metricsParams = useMemo(
    () => ({
      projectIds: parsedProjectIds,
      fromDate: fromDate ? `${fromDate}T00:00:00Z` : null,
      toDate: toDate ? `${toDate}T23:59:59Z` : null
    }),
    [parsedProjectIds, fromDate, toDate]
  );

  const metricsQuery = useMetricsSummaryQuery(metricsParams);
  const evalQuery = useEvalArtifactsQuery();
  const extractMutation = useExtractMutation();

  const byProjectColumns = useMemo(
    () => [
      { key: "project", header: "Project", render: (row: MetricsSummaryByProject) => row.project_id },
      { key: "issues", header: "Issues", render: (row: MetricsSummaryByProject) => row.issues_total },
      {
        key: "first_response",
        header: "Avg first response",
        render: (row: MetricsSummaryByProject) => formatDurationSeconds(row.avg_first_response_s)
      },
      {
        key: "resolution",
        header: "Avg resolution",
        render: (row: MetricsSummaryByProject) => formatDurationSeconds(row.avg_resolution_s)
      },
      { key: "reopen", header: "Reopens", render: (row: MetricsSummaryByProject) => row.reopen_total },
      { key: "touch", header: "Touches", render: (row: MetricsSummaryByProject) => row.touch_total },
      { key: "handoff", header: "Handoffs", render: (row: MetricsSummaryByProject) => row.handoff_total }
    ],
    []
  );

  const comparisonColumns = useMemo(
    () => [
      {
        key: "metric",
        header: "Metric",
        render: (row: EvalComparisonRow) => metricLabel(row.metric)
      },
      {
        key: "baseline",
        header: "Baseline",
        render: (row: EvalComparisonRow) => formatPercent(row.baseline)
      },
      {
        key: "current",
        header: "Current",
        render: (row: EvalComparisonRow) => formatPercent(row.current)
      },
      {
        key: "delta",
        header: "Delta",
        render: (row: EvalComparisonRow) => `${row.delta >= 0 ? "+" : ""}${formatPercent(row.delta)}`
      },
      {
        key: "threshold",
        header: "Allowed drop",
        render: (row: EvalComparisonRow) => formatPercent(row.allowed_drop)
      },
      {
        key: "status",
        header: "Status",
        render: (row: EvalComparisonRow) => (
          <span
            className={[
              "rounded-full px-2 py-1 text-xs font-semibold",
              row.passed ? "bg-[var(--success-soft)] text-[#1d5f1f]" : "bg-[var(--danger-soft)] text-[var(--danger-ink)]"
            ].join(" ")}
          >
            {row.passed ? "pass" : "fail"}
          </span>
        )
      }
    ],
    []
  );

  const evalStatusPill = useMemo(() => {
    const status = evalQuery.data?.status ?? "missing";
    if (status === "pass") {
      return <span className="rounded-full bg-[var(--success-soft)] px-3 py-1 text-sm font-semibold text-[#1d5f1f]">PASS</span>;
    }
    if (status === "fail") {
      return <span className="rounded-full bg-[var(--danger-soft)] px-3 py-1 text-sm font-semibold text-[var(--danger-ink)]">FAIL</span>;
    }
    return <span className="rounded-full bg-[var(--surface-2)] px-3 py-1 text-sm font-semibold text-[var(--ink-2)]">MISSING</span>;
  }, [evalQuery.data?.status]);

  const refreshAll = () => {
    setLastManualRefreshAt(new Date().toISOString());
    void metricsQuery.refetch();
    void evalQuery.refetch();
  };

  const runExtraction = () => {
    const issueIds = parseExtractionIssueIds(extractIssueIds);
    extractMutation.mutate(
      { issue_ids: issueIds },
      {
        onSuccess: (response) => {
          setLatestExtraction({
            requestedIssueIds: issueIds,
            processedIssues: response.processed_issues,
            detail: response.detail,
            finishedAt: new Date().toISOString(),
            counters: parseExtractionCounters(response.detail)
          });
          void metricsQuery.refetch();
        }
      }
    );
  };

  const metricsUpdatedLabel =
    metricsQuery.dataUpdatedAt > 0 ? new Date(metricsQuery.dataUpdatedAt).toLocaleString() : "-";
  const evalUpdatedLabel =
    evalQuery.dataUpdatedAt > 0 ? new Date(evalQuery.dataUpdatedAt).toLocaleString() : "-";

  return (
    <div className="space-y-6">
      <PageHeader
        title="Metrics, Extraction, and Evaluation Dashboard"
        subtitle="Track quality metrics, run extraction control actions, inspect LLM extraction health counters, and monitor regression gate status."
        actions={
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={refreshAll}>
              Refresh now
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                if (!metricsQuery.data) {
                  return;
                }
                downloadJson("metrics-summary.snapshot.json", metricsQuery.data);
              }}
              disabled={!metricsQuery.data}
            >
              Export metrics
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                if (!evalQuery.data) {
                  return;
                }
                downloadJson("eval-regression.snapshot.json", evalQuery.data);
              }}
              disabled={!evalQuery.data}
            >
              Export eval
            </Button>
          </div>
        }
      />

      <Card title="Filter Window" description="Deterministic filter scope for reproducible summaries.">
        <form
          className="space-y-4"
          onSubmit={(event) => {
            event.preventDefault();
            void metricsQuery.refetch();
          }}
        >
          <div className="grid gap-4 md:grid-cols-3">
            <TextField
              label="Project IDs"
              name="projectIds"
              value={projectIds}
              onChange={(event) => setProjectIds(event.target.value)}
              hint="Comma-separated; empty = all projects"
            />
            <TextField
              label="From date"
              name="fromDate"
              type="date"
              value={fromDate}
              onChange={(event) => setFromDate(event.target.value)}
            />
            <TextField
              label="To date"
              name="toDate"
              type="date"
              value={toDate}
              onChange={(event) => setToDate(event.target.value)}
            />
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <Button type="submit" disabled={metricsQuery.isFetching}>
              Apply filters
            </Button>
            <p className="text-xs text-[var(--ink-2)]">
              Auto refresh: metrics 60s, eval 90s. Last manual refresh:{" "}
              {lastManualRefreshAt ? new Date(lastManualRefreshAt).toLocaleString() : "-"}.
            </p>
          </div>
        </form>
      </Card>

      {(metricsQuery.isLoading || evalQuery.isLoading) && (
        <LoadingState label="Loading dashboard data" />
      )}
      {metricsQuery.isError ? (
        <ErrorState
          message={toUserMessage(metricsQuery.error)}
          onRetry={() => {
            void metricsQuery.refetch();
          }}
        />
      ) : null}
      {evalQuery.isError ? (
        <ErrorState
          message={toUserMessage(evalQuery.error)}
          onRetry={() => {
            void evalQuery.refetch();
          }}
        />
      ) : null}

      {metricsQuery.data ? (
        <>
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <Card title="Issues total" description={`updated ${metricsUpdatedLabel}`}>
              <p className="text-2xl font-semibold text-[var(--ink-1)]">{metricsQuery.data.issues_total}</p>
            </Card>
            <Card title="Avg first response" description="Extracted from deterministic properties">
              <p className="text-2xl font-semibold text-[var(--ink-1)]">
                {formatDurationSeconds(metricsQuery.data.avg_first_response_s)}
              </p>
            </Card>
            <Card title="Avg resolution" description="Extracted from deterministic properties">
              <p className="text-2xl font-semibold text-[var(--ink-1)]">
                {formatDurationSeconds(metricsQuery.data.avg_resolution_s)}
              </p>
            </Card>
            <Card title="Reopen / Touch / Handoff" description={`Extractor ${metricsQuery.data.extractor_version}`}>
              <p className="text-sm text-[var(--ink-1)]">
                {metricsQuery.data.reopen_total} / {metricsQuery.data.touch_total} / {metricsQuery.data.handoff_total}
              </p>
            </Card>
          </section>

          <Card
            title="Per-Project Breakdown"
            description={`Scope project_ids=${metricsQuery.data.project_ids.join(", ") || "all"} | from=${metricsQuery.data.from_date ?? "none"} | to=${metricsQuery.data.to_date ?? "none"}`}
          >
            {metricsQuery.data.by_project.length === 0 ? (
              <EmptyState
                title="No metrics in selected window"
                description="Adjust project/date filters to include extracted issue properties."
              />
            ) : (
              <DataTable
                columns={byProjectColumns}
                items={metricsQuery.data.by_project}
                rowKey={(row) => String(row.project_id)}
              />
            )}
          </Card>
        </>
      ) : null}

      <Card
        title="Extraction Control"
        description="Run property extraction and inspect latest extraction diagnostics without terminal access."
      >
        <form
          className="space-y-3"
          onSubmit={(event) => {
            event.preventDefault();
            runExtraction();
          }}
        >
          <TextField
            label="Issue IDs (optional)"
            name="extractIssueIds"
            value={extractIssueIds}
            onChange={(event) => setExtractIssueIds(event.target.value)}
            hint="Comma-separated; empty runs extraction for all issues."
          />
          <Button type="submit" disabled={extractMutation.isPending}>
            {extractMutation.isPending ? "Running extraction…" : "Run extraction"}
          </Button>
        </form>

        {extractMutation.isError ? (
          <p className="mt-3 text-sm text-[var(--danger-ink)]">{toUserMessage(extractMutation.error)}</p>
        ) : null}

        {latestExtraction ? (
          <div className="mt-4 space-y-3 rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4">
            <p className="text-sm text-[var(--ink-1)]">
              Latest run at {new Date(latestExtraction.finishedAt).toLocaleString()} | processed{" "}
              {latestExtraction.processedIssues} issues | scope{" "}
              {latestExtraction.requestedIssueIds?.join(", ") ?? "all"}.
            </p>
            <p className="text-sm text-[var(--ink-1)]">{latestExtraction.detail}</p>
            <div className="grid gap-2 sm:grid-cols-4">
              <div className="rounded-lg bg-[var(--surface-0)] px-3 py-2 text-sm text-[var(--ink-1)]">
                success: {latestExtraction.counters?.success ?? 0}
              </div>
              <div className="rounded-lg bg-[var(--surface-0)] px-3 py-2 text-sm text-[var(--ink-1)]">
                failed: {latestExtraction.counters?.failed ?? 0}
              </div>
              <div className="rounded-lg bg-[var(--surface-0)] px-3 py-2 text-sm text-[var(--ink-1)]">
                skipped: {latestExtraction.counters?.skipped ?? 0}
              </div>
              <div className="rounded-lg bg-[var(--surface-0)] px-3 py-2 text-sm text-[var(--ink-1)]">
                retries: {latestExtraction.counters?.retries ?? 0}
              </div>
            </div>
          </div>
        ) : (
          <p className="mt-3 text-sm text-[var(--ink-2)]">No extraction run from UI yet.</p>
        )}
      </Card>

      <Card
        title="Evaluation and Regression Gate"
        description={`Latest eval artifact update: ${evalUpdatedLabel}`}
      >
        {evalQuery.data ? (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-sm text-[var(--ink-1)]">Gate status:</span>
              {evalStatusPill}
            </div>

            {evalQuery.data.current_metrics ? (
              <section className="grid gap-3 md:grid-cols-3">
                <div className="rounded-xl bg-[var(--surface-1)] p-3">
                  <p className="text-xs uppercase tracking-wide text-[var(--ink-2)]">Citation coverage</p>
                  <p className="text-lg font-semibold text-[var(--ink-1)]">
                    {formatPercent(evalQuery.data.current_metrics.citation_coverage)}
                  </p>
                </div>
                <div className="rounded-xl bg-[var(--surface-1)] p-3">
                  <p className="text-xs uppercase tracking-wide text-[var(--ink-2)]">Groundedness</p>
                  <p className="text-lg font-semibold text-[var(--ink-1)]">
                    {formatPercent(evalQuery.data.current_metrics.groundedness)}
                  </p>
                </div>
                <div className="rounded-xl bg-[var(--surface-1)] p-3">
                  <p className="text-xs uppercase tracking-wide text-[var(--ink-2)]">Retrieval hit rate</p>
                  <p className="text-lg font-semibold text-[var(--ink-1)]">
                    {formatPercent(evalQuery.data.current_metrics.retrieval_hit_rate)}
                  </p>
                </div>
              </section>
            ) : (
              <EmptyState
                title="No eval metrics report"
                description="Run `make eval` to generate latest eval report artifacts."
              />
            )}

            {evalQuery.data.comparisons.length > 0 ? (
              <DataTable
                columns={comparisonColumns}
                items={evalQuery.data.comparisons}
                rowKey={(row) => row.metric}
              />
            ) : null}

            {evalQuery.data.failures.length > 0 ? (
              <div className="rounded-xl bg-[var(--danger-soft)] p-3 text-sm text-[var(--danger-ink)]">
                <p className="font-semibold">Failures</p>
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  {evalQuery.data.failures.map((failure) => (
                    <li key={failure}>{failure}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {evalQuery.data.notes.length > 0 ? (
              <div className="rounded-xl bg-[var(--surface-2)] p-3 text-sm text-[var(--ink-2)]">
                <p className="font-semibold text-[var(--ink-1)]">Notes</p>
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  {evalQuery.data.notes.map((note) => (
                    <li key={note}>{note}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            <Button
              variant="secondary"
              onClick={() => {
                if (!evalQuery.data) {
                  return;
                }
                downloadJson(
                  "dashboard-metrics-eval.snapshot.json",
                  buildMetricsExportPayload({
                    generatedAt: metricsQuery.data?.generated_at ?? evalQuery.data.generated_at,
                    projectIds: parsedProjectIds,
                    fromDate: metricsParams.fromDate,
                    toDate: metricsParams.toDate,
                    metrics: evalQuery.data.current_metrics,
                    comparisons: evalQuery.data.comparisons
                  })
                );
              }}
              disabled={!evalQuery.data}
            >
              Export combined snapshot
            </Button>
          </div>
        ) : (
          <EmptyState
            title="No eval status yet"
            description="Refresh once eval artifacts are available."
          />
        )}
      </Card>
    </div>
  );
}
