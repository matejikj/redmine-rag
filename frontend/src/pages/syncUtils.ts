import type { SyncJobResponse, SyncModule, SyncRequest } from "../lib/api/types";

export interface SyncSummary {
  modulesEnabled: string[];
  modulesSkipped: Array<{ module: string; reason: string; status_code?: number }>;
  entities: Array<{ label: string; value: number }>;
  indexing: Array<{ label: string; value: number }>;
}

const ENTITY_KEYS: Array<{ key: string; label: string }> = [
  { key: "projects_synced", label: "Projects" },
  { key: "users_synced", label: "Users" },
  { key: "groups_synced", label: "Groups" },
  { key: "issues_synced", label: "Issues" },
  { key: "journals_synced", label: "Journals" },
  { key: "attachments_synced", label: "Attachments" },
  { key: "news_synced", label: "News" },
  { key: "documents_synced", label: "Documents" },
  { key: "files_synced", label: "Files" },
  { key: "wiki_pages_synced", label: "Wiki pages" }
];

const INDEX_KEYS: Array<{ key: string; label: string }> = [
  { key: "chunk_sources_reindexed", label: "Sources reindexed" },
  { key: "chunks_updated", label: "Chunks updated" },
  { key: "embeddings_processed", label: "Embeddings processed" },
  { key: "vectors_upserted", label: "Vectors upserted" },
  { key: "vectors_removed", label: "Vectors removed" }
];

export function parseProjectScope(value: string): number[] {
  return value
    .split(",")
    .map((item) => Number.parseInt(item.trim(), 10))
    .filter((item) => Number.isFinite(item) && item > 0);
}

export function extractModulesFromPayload(payload: Record<string, unknown>): string[] {
  const rawModules = payload.modules;
  if (!Array.isArray(rawModules)) {
    return [];
  }
  return rawModules.map((module) => String(module));
}

export function extractSyncSummary(payload: Record<string, unknown>): SyncSummary | null {
  const summary = payload.summary;
  if (!summary || typeof summary !== "object") {
    return null;
  }

  const summaryRecord = summary as Record<string, unknown>;
  const entities = ENTITY_KEYS.map(({ key, label }) => ({
    label,
    value: toNumber(summaryRecord[key])
  }));

  const indexing = INDEX_KEYS.map(({ key, label }) => ({
    label,
    value: toNumber(summaryRecord[key])
  }));

  const rawModulesEnabled = summaryRecord.modules_enabled;
  const modulesEnabled = Array.isArray(rawModulesEnabled)
    ? rawModulesEnabled.map((module) => String(module))
    : [];

  const rawModulesSkipped = summaryRecord.modules_skipped;
  const modulesSkipped = Array.isArray(rawModulesSkipped)
    ? rawModulesSkipped
        .filter((item) => item && typeof item === "object")
        .map((item) => {
          const record = item as Record<string, unknown>;
          return {
            module: String(record.module ?? "unknown"),
            reason: String(record.reason ?? "unknown"),
            status_code: record.status_code ? toNumber(record.status_code) : undefined
          };
        })
    : [];

  return {
    modulesEnabled,
    modulesSkipped,
    entities,
    indexing
  };
}

export function buildRetryPayload(job: SyncJobResponse): SyncRequest {
  const projectIds = Array.isArray(job.payload.project_ids)
    ? job.payload.project_ids
        .map((item) => Number.parseInt(String(item), 10))
        .filter((item) => Number.isFinite(item) && item > 0)
    : [];
  const modules = extractModulesFromPayload(job.payload);

  return {
    project_ids: projectIds.length > 0 ? projectIds : null,
    modules: modules.length > 0 ? modules : null
  };
}

export function getFailureRecommendations(job: SyncJobResponse): string[] {
  if (job.status !== "failed") {
    return [];
  }
  const recommendations: string[] = [];
  const errorText = `${job.error_message ?? ""} ${String(job.payload.error_type ?? "")}`.toLowerCase();

  if (errorText.includes("connect") || errorText.includes("timeout") || errorText.includes("network")) {
    recommendations.push("Check REDMINE_BASE_URL connectivity and retry the job.");
    recommendations.push("Verify REDMINE_API_KEY and outbound host policy in /healthz.");
  }
  if (errorText.includes("keyerror") || errorText.includes("schema") || errorText.includes("json")) {
    recommendations.push("Inspect payload schema mismatch in logs and confirm Redmine response shape.");
  }
  if (errorText.includes("unauthorized") || errorText.includes("forbidden") || errorText.includes("401")) {
    recommendations.push("Rotate API key and verify account permissions for requested modules.");
  }

  if (recommendations.length === 0) {
    recommendations.push("Inspect the backend logs for the job_id and retry after remediation.");
  }

  return recommendations;
}

export function formatDuration(startedAt: string | null, finishedAt: string | null): string {
  if (!startedAt || !finishedAt) {
    return "-";
  }
  const start = Date.parse(startedAt);
  const end = Date.parse(finishedAt);
  if (Number.isNaN(start) || Number.isNaN(end) || end < start) {
    return "-";
  }
  const seconds = Math.round((end - start) / 1000);
  return `${seconds}s`;
}

function toNumber(value: unknown): number {
  if (typeof value === "number" && Number.isFinite(value)) {
    return Math.trunc(value);
  }
  if (typeof value === "string") {
    const parsed = Number.parseInt(value, 10);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return 0;
}

export function toSyncModuleSet(modules: readonly SyncModule[], selected: string[]): Set<SyncModule> {
  const selectedSet = new Set<string>(selected);
  return new Set(modules.filter((module) => selectedSet.has(module)));
}
