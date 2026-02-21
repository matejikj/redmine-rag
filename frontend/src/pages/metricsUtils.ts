import type { EvalComparisonRow, EvalMetricsSnapshot } from "../lib/api/types";

const EXTRACTION_COUNTERS_PATTERN = /LLM ok=(\d+),\s*failed=(\d+),\s*skipped=(\d+),\s*retries=(\d+)/i;

export interface ExtractionCounters {
  success: number;
  failed: number;
  skipped: number;
  retries: number;
}

export function parseCsvIds(value: string): number[] {
  return value
    .split(",")
    .map((item) => Number.parseInt(item.trim(), 10))
    .filter((item) => Number.isFinite(item) && item > 0);
}

export function parseExtractionIssueIds(value: string): number[] | null {
  const parsed = parseCsvIds(value);
  return parsed.length > 0 ? parsed : null;
}

export function parseExtractionCounters(detail: string): ExtractionCounters | null {
  const matched = detail.match(EXTRACTION_COUNTERS_PATTERN);
  if (!matched) {
    return null;
  }
  return {
    success: Number.parseInt(matched[1], 10),
    failed: Number.parseInt(matched[2], 10),
    skipped: Number.parseInt(matched[3], 10),
    retries: Number.parseInt(matched[4], 10)
  };
}

export function formatDurationSeconds(seconds: number | null): string {
  if (seconds === null || !Number.isFinite(seconds)) {
    return "-";
  }
  if (seconds < 60) {
    return `${seconds.toFixed(0)}s`;
  }
  const minutes = seconds / 60;
  if (minutes < 60) {
    return `${minutes.toFixed(1)}m`;
  }
  const hours = minutes / 60;
  return `${hours.toFixed(1)}h`;
}

export function formatPercent(value: number): string {
  if (!Number.isFinite(value)) {
    return "0%";
  }
  return `${(value * 100).toFixed(1)}%`;
}

export function metricLabel(metric: string): string {
  if (metric === "citation_coverage") {
    return "Citation coverage";
  }
  if (metric === "groundedness") {
    return "Groundedness";
  }
  if (metric === "retrieval_hit_rate") {
    return "Retrieval hit rate";
  }
  return metric;
}

export function buildMetricsExportPayload(input: {
  generatedAt: string;
  projectIds: number[];
  fromDate: string | null;
  toDate: string | null;
  metrics: EvalMetricsSnapshot | null;
  comparisons: EvalComparisonRow[];
}): Record<string, unknown> {
  return {
    exported_at: new Date().toISOString(),
    generated_at: input.generatedAt,
    filters: {
      project_ids: input.projectIds,
      from_date: input.fromDate,
      to_date: input.toDate
    },
    metrics: input.metrics,
    comparisons: input.comparisons
  };
}
