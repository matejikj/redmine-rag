import { describe, expect, it } from "vitest";

import {
  formatDurationSeconds,
  formatPercent,
  metricLabel,
  parseCsvIds,
  parseExtractionCounters,
  parseExtractionIssueIds
} from "../metricsUtils";

describe("metricsUtils", () => {
  it("parses positive IDs from csv fields", () => {
    expect(parseCsvIds("1, 2, x, 0, 9")).toEqual([1, 2, 9]);
    expect(parseExtractionIssueIds("")).toBeNull();
  });

  it("parses extraction counters from detail string", () => {
    const counters = parseExtractionCounters(
      "Deterministic extraction completed. LLM ok=11, failed=2, skipped=1, retries=4."
    );
    expect(counters).toEqual({
      success: 11,
      failed: 2,
      skipped: 1,
      retries: 4
    });
    expect(parseExtractionCounters("no llm detail present")).toBeNull();
  });

  it("formats durations, percentages and metric labels", () => {
    expect(formatDurationSeconds(42)).toBe("42s");
    expect(formatDurationSeconds(120)).toBe("2.0m");
    expect(formatDurationSeconds(7200)).toBe("2.0h");
    expect(formatPercent(0.925)).toBe("92.5%");
    expect(metricLabel("retrieval_hit_rate")).toBe("Retrieval hit rate");
  });
});
