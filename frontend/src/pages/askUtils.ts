import type { Citation } from "../lib/api/types";

const CLAIM_LINE_PATTERN = /^(\d+)\.\s(.+?)\s\[(\d+(?:,\s*\d+)*)\]$/;
const RETRIEVAL_DIAGNOSTICS_PATTERN =
  /Retrieval mode:\s*([a-z_]+);\s*lexical=(\d+),\s*vector=(\d+),\s*fused=(\d+)/i;

export interface ParsedClaim {
  index: number;
  text: string;
  citationIds: number[];
}

export interface RetrievalDiagnostics {
  mode: string | null;
  lexical: number | null;
  vector: number | null;
  fused: number | null;
}

export type CitationSort = "id_asc" | "source_type" | "snippet_length_desc";

export function parseCsvIds(value: string): number[] {
  return value
    .split(",")
    .map((item) => Number.parseInt(item.trim(), 10))
    .filter((item) => Number.isFinite(item) && item > 0);
}

export function parseClaimsFromMarkdown(markdown: string): ParsedClaim[] {
  return markdown
    .split("\n")
    .map((line) => line.trim())
    .map((line) => {
      const matched = line.match(CLAIM_LINE_PATTERN);
      if (!matched) {
        return null;
      }
      const index = Number.parseInt(matched[1], 10);
      const text = matched[2].trim();
      const citationIds = matched[3]
        .split(",")
        .map((item) => Number.parseInt(item.trim(), 10))
        .filter((item) => Number.isFinite(item) && item > 0);
      return {
        index,
        text,
        citationIds
      } satisfies ParsedClaim;
    })
    .filter((item): item is ParsedClaim => item !== null);
}

export function parseRetrievalDiagnostics(markdown: string): RetrievalDiagnostics {
  const line = markdown
    .split("\n")
    .find((rawLine) => rawLine.toLowerCase().includes("retrieval mode:"));
  if (!line) {
    return {
      mode: null,
      lexical: null,
      vector: null,
      fused: null
    };
  }
  const matched = line.match(RETRIEVAL_DIAGNOSTICS_PATTERN);
  if (!matched) {
    return {
      mode: null,
      lexical: null,
      vector: null,
      fused: null
    };
  }
  return {
    mode: matched[1],
    lexical: Number.parseInt(matched[2], 10),
    vector: Number.parseInt(matched[3], 10),
    fused: Number.parseInt(matched[4], 10)
  };
}

export function detectSynthesisMode(markdown: string): "llm" | "deterministic" | "fallback" | "unknown" {
  const lowered = markdown.toLowerCase();
  if (lowered.includes("odpověď podložená redmine zdroji (llm)")) {
    return "llm";
  }
  if (lowered.includes("bezpečnostní fallback") || lowered.includes("llm runtime")) {
    return "fallback";
  }
  if (lowered.includes("odpověď podložená redmine zdroji")) {
    return "deterministic";
  }
  return "unknown";
}

export function sortAndFilterCitations(
  citations: Citation[],
  {
    sortBy,
    sourceType,
    search,
    allowIds
  }: {
    sortBy: CitationSort;
    sourceType: string;
    search: string;
    allowIds: Set<number> | null;
  }
): Citation[] {
  const normalizedSearch = search.trim().toLowerCase();
  const filtered = citations.filter((citation) => {
    if (sourceType !== "all" && citation.source_type !== sourceType) {
      return false;
    }
    if (allowIds && !allowIds.has(citation.id)) {
      return false;
    }
    if (!normalizedSearch) {
      return true;
    }
    const corpus = `${citation.source_type} ${citation.source_id} ${citation.snippet}`.toLowerCase();
    return corpus.includes(normalizedSearch);
  });

  const sorted = [...filtered];
  if (sortBy === "id_asc") {
    sorted.sort((left, right) => left.id - right.id);
  } else if (sortBy === "source_type") {
    sorted.sort((left, right) => {
      const sourceCompare = left.source_type.localeCompare(right.source_type);
      if (sourceCompare !== 0) {
        return sourceCompare;
      }
      return left.id - right.id;
    });
  } else {
    sorted.sort((left, right) => right.snippet.length - left.snippet.length || left.id - right.id);
  }
  return sorted;
}

export function getCitedSourceTypeCoverage(citations: Citation[]): Record<string, number> {
  return citations.reduce<Record<string, number>>((accumulator, citation) => {
    accumulator[citation.source_type] = (accumulator[citation.source_type] ?? 0) + 1;
    return accumulator;
  }, {});
}
