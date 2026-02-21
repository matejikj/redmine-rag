export type HealthStatus = "ok" | "warn" | "fail";

export interface HealthCheck {
  name: string;
  status: HealthStatus;
  detail: string | null;
  latency_ms: number | null;
}

export interface SyncJobCounts {
  queued: number;
  running: number;
  finished: number;
  failed: number;
}

export interface HealthResponse {
  status: "ok" | "degraded" | "fail";
  app: string;
  version: string;
  utc_time: string;
  checks: HealthCheck[];
  sync_jobs: SyncJobCounts;
}

export interface OpsEnvironmentResponse {
  generated_at: string;
  app: string;
  version: string;
  app_env: string;
  redmine_base_url: string;
  redmine_allowed_hosts: string[];
  llm_provider: string;
  llm_model: string;
  llm_extract_enabled: boolean;
}

export interface OpsBackupRequest {
  output_dir: string | null;
}

export interface OpsRunRecord {
  id: string;
  action: "backup" | "maintenance";
  status: "success" | "failed";
  started_at: string;
  finished_at: string;
  detail: string;
  summary: Record<string, unknown>;
}

export interface OpsActionResponse {
  accepted: boolean;
  run: OpsRunRecord;
}

export interface OpsRunListResponse {
  items: OpsRunRecord[];
  total: number;
}

export interface AskFilters {
  project_ids: number[];
  tracker_ids: number[];
  status_ids: number[];
  from_date: string | null;
  to_date: string | null;
}

export interface AskRequest {
  query: string;
  filters: AskFilters;
  top_k: number;
}

export interface Citation {
  id: number;
  url: string;
  source_type: string;
  source_id: string;
  snippet: string;
}

export interface AskResponse {
  answer_markdown: string;
  citations: Citation[];
  used_chunk_ids: number[];
  confidence: number;
}

export interface SyncRequest {
  project_ids: number[] | null;
  modules: string[] | null;
}

export interface SyncResponse {
  job_id: string;
  accepted: boolean;
  detail: string;
}

export interface SyncJobResponse {
  id: string;
  status: "queued" | "running" | "finished" | "failed" | string;
  payload: Record<string, unknown>;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface SyncJobListResponse {
  items: SyncJobResponse[];
  total: number;
  counts: SyncJobCounts;
}

export interface ExtractRequest {
  issue_ids: number[] | null;
}

export interface ExtractResponse {
  accepted: boolean;
  processed_issues: number;
  detail: string;
}

export interface MetricsSummaryByProject {
  project_id: number;
  issues_total: number;
  issues_with_first_response: number;
  issues_with_resolution: number;
  avg_first_response_s: number | null;
  avg_resolution_s: number | null;
  reopen_total: number;
  touch_total: number;
  handoff_total: number;
}

export interface MetricsSummaryResponse {
  generated_at: string;
  from_date: string | null;
  to_date: string | null;
  project_ids: number[];
  extractor_version: string;
  issues_total: number;
  issues_with_first_response: number;
  issues_with_resolution: number;
  avg_first_response_s: number | null;
  avg_resolution_s: number | null;
  reopen_total: number;
  touch_total: number;
  handoff_total: number;
  by_project: MetricsSummaryByProject[];
}

export interface EvalMetricsSnapshot {
  query_count: number;
  citation_coverage: number;
  groundedness: number;
  retrieval_hit_rate: number;
  source_type_coverage: Record<string, number>;
}

export interface EvalComparisonRow {
  metric: string;
  baseline: number;
  current: number;
  delta: number;
  allowed_drop: number;
  passed: boolean;
}

export interface EvalArtifactsResponse {
  generated_at: string;
  status: "pass" | "fail" | "missing";
  current_report_path: string | null;
  baseline_path: string | null;
  regression_gate_path: string | null;
  current_metrics: EvalMetricsSnapshot | null;
  baseline_metrics: EvalMetricsSnapshot | null;
  comparisons: EvalComparisonRow[];
  failures: string[];
  llm_runtime_failures: string[];
  notes: string[];
}

export const SYNC_MODULES = [
  "projects",
  "users",
  "groups",
  "trackers",
  "issue_statuses",
  "issue_priorities",
  "issues",
  "time_entries",
  "news",
  "documents",
  "files",
  "boards",
  "wiki"
] as const;

export type SyncModule = (typeof SYNC_MODULES)[number];
