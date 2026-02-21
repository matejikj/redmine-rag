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
