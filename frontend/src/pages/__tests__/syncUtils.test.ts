import { describe, expect, it } from "vitest";

import type { SyncJobResponse } from "../../lib/api/types";
import {
  buildRetryPayload,
  extractModulesFromPayload,
  extractSyncSummary,
  formatDuration,
  getFailureRecommendations,
  parseProjectScope
} from "../syncUtils";

describe("syncUtils", () => {
  it("parses project scope", () => {
    expect(parseProjectScope("1, 2,abc,0, 9")).toEqual([1, 2, 9]);
  });

  it("extracts modules and sync summary", () => {
    const payload = {
      modules: ["issues", "news"],
      summary: {
        modules_enabled: ["issues", "news"],
        modules_skipped: [{ module: "wiki", reason: "no_wiki_pages_configured" }],
        issues_synced: 3,
        chunk_sources_reindexed: 10,
        vectors_upserted: 5
      }
    } as Record<string, unknown>;

    expect(extractModulesFromPayload(payload)).toEqual(["issues", "news"]);
    const summary = extractSyncSummary(payload);
    expect(summary).not.toBeNull();
    expect(summary?.modulesEnabled).toEqual(["issues", "news"]);
    expect(summary?.modulesSkipped[0].module).toBe("wiki");
  });

  it("builds retry payload from selected job", () => {
    const job = {
      id: "job-1",
      status: "failed",
      payload: { project_ids: [1, 2], modules: ["issues"] },
      started_at: null,
      finished_at: null,
      error_message: "timeout",
      created_at: "2026-02-21T10:00:00Z",
      updated_at: "2026-02-21T10:00:00Z"
    } satisfies SyncJobResponse;

    expect(buildRetryPayload(job)).toEqual({
      project_ids: [1, 2],
      modules: ["issues"]
    });
  });

  it("generates failure recommendations", () => {
    const job = {
      id: "job-2",
      status: "failed",
      payload: { error_type: "ConnectError" },
      started_at: null,
      finished_at: null,
      error_message: "network timeout",
      created_at: "2026-02-21T10:00:00Z",
      updated_at: "2026-02-21T10:00:00Z"
    } satisfies SyncJobResponse;

    expect(getFailureRecommendations(job).length).toBeGreaterThan(0);
  });

  it("formats duration", () => {
    expect(formatDuration("2026-02-21T10:00:00Z", "2026-02-21T10:00:30Z")).toBe("30s");
  });
});
