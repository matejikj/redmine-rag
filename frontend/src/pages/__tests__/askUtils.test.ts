import { describe, expect, it } from "vitest";

import type { Citation } from "../../lib/api/types";
import {
  detectSynthesisMode,
  parseClaimsFromMarkdown,
  parseRetrievalDiagnostics,
  sortAndFilterCitations
} from "../askUtils";

describe("askUtils", () => {
  it("parses claims and citation ids from markdown", () => {
    const claims = parseClaimsFromMarkdown(
      [
        "### Odpověď podložená Redmine zdroji (LLM)",
        "1. OAuth callback timeout affects Safari login flow. [1, 2]",
        "2. Rollback is documented in incident runbook. [3]"
      ].join("\n")
    );

    expect(claims).toEqual([
      { index: 1, text: "OAuth callback timeout affects Safari login flow.", citationIds: [1, 2] },
      { index: 2, text: "Rollback is documented in incident runbook.", citationIds: [3] }
    ]);
  });

  it("extracts retrieval diagnostics and synthesis mode", () => {
    const markdown =
      "_Retrieval mode: hybrid; lexical=14, vector=9, fused=5_\n### Odpověď podložená Redmine zdroji (LLM)";

    expect(parseRetrievalDiagnostics(markdown)).toEqual({
      mode: "hybrid",
      lexical: 14,
      vector: 9,
      fused: 5
    });
    expect(detectSynthesisMode(markdown)).toBe("llm");
  });

  it("sorts and filters citations", () => {
    const citations: Citation[] = [
      { id: 2, url: "u2", source_type: "wiki", source_id: "w1", snippet: "rollback plan" },
      { id: 1, url: "u1", source_type: "issue", source_id: "i1", snippet: "oauth callback" }
    ];

    const result = sortAndFilterCitations(citations, {
      sortBy: "source_type",
      sourceType: "all",
      search: "oauth",
      allowIds: null
    });

    expect(result).toEqual([
      { id: 1, url: "u1", source_type: "issue", source_id: "i1", snippet: "oauth callback" }
    ]);
  });
});
