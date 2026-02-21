import { useEffect, useMemo, useState } from "react";

import { CitationCard } from "../components/domain/CitationCard";
import { PageHeader } from "../components/layout/PageHeader";
import { EmptyState } from "../components/states/EmptyState";
import { ErrorState } from "../components/states/ErrorState";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { MarkdownSurface } from "../components/ui/MarkdownSurface";
import { SelectField } from "../components/ui/SelectField";
import { TextAreaField } from "../components/ui/TextAreaField";
import { TextField } from "../components/ui/TextField";
import { useAskMutation } from "../lib/api/hooks";
import type { Citation } from "../lib/api/types";
import { toUserMessage } from "../lib/utils/errors";
import {
  detectSynthesisMode,
  getCitedSourceTypeCoverage,
  parseClaimsFromMarkdown,
  parseCsvIds,
  parseRetrievalDiagnostics,
  sortAndFilterCitations,
  type CitationSort
} from "./askUtils";

interface AskHistoryItem {
  query: string;
  projectIds: string;
  trackerIds: string;
  statusIds: string;
  topK: string;
  fromDate: string;
  toDate: string;
  at: string;
}

const HISTORY_KEY = "redmine-rag.ask-history.v2";
const QUICK_PROMPTS = [
  "What is the login callback issue and rollback plan?",
  "Which issue documents incident triage for OAuth failures?",
  "What evidence points to root cause and mitigation steps?",
  "Summarize user impact and next actions for the latest auth incident.",
  "What changed between initial incident and final resolution?"
];

export function AskPage() {
  const [query, setQuery] = useState(QUICK_PROMPTS[0]);
  const [projectIds, setProjectIds] = useState("1");
  const [trackerIds, setTrackerIds] = useState("");
  const [statusIds, setStatusIds] = useState("");
  const [topK, setTopK] = useState("5");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [history, setHistory] = useState<AskHistoryItem[]>([]);
  const [debugMode, setDebugMode] = useState(false);

  const [citationDrawerOpen, setCitationDrawerOpen] = useState(true);
  const [citationSort, setCitationSort] = useState<CitationSort>("id_asc");
  const [citationSourceFilter, setCitationSourceFilter] = useState("all");
  const [citationSearch, setCitationSearch] = useState("");
  const [onlyActiveClaimEvidence, setOnlyActiveClaimEvidence] = useState(false);
  const [activeClaimIndex, setActiveClaimIndex] = useState<number | null>(null);
  const [activeCitationId, setActiveCitationId] = useState<number | null>(null);

  const askMutation = useAskMutation();

  useEffect(() => {
    const raw = window.localStorage.getItem(HISTORY_KEY);
    if (!raw) {
      return;
    }
    try {
      const parsed = JSON.parse(raw) as AskHistoryItem[];
      setHistory(parsed.slice(0, 12));
    } catch {
      setHistory([]);
    }
  }, []);

  const claims = useMemo(() => {
    const markdown = askMutation.data?.answer_markdown;
    if (!markdown) {
      return [];
    }
    return parseClaimsFromMarkdown(markdown);
  }, [askMutation.data?.answer_markdown]);

  const activeClaim = useMemo(
    () => claims.find((claim) => claim.index === activeClaimIndex) ?? null,
    [claims, activeClaimIndex]
  );

  useEffect(() => {
    if (!askMutation.data) {
      return;
    }
    if (claims.length > 0) {
      setActiveClaimIndex(claims[0].index);
      setActiveCitationId(claims[0].citationIds[0] ?? null);
    } else {
      setActiveClaimIndex(null);
      setActiveCitationId(askMutation.data.citations[0]?.id ?? null);
    }
  }, [askMutation.data, claims]);

  const retrievalDiagnostics = useMemo(() => {
    return parseRetrievalDiagnostics(askMutation.data?.answer_markdown ?? "");
  }, [askMutation.data?.answer_markdown]);

  const synthesisMode = useMemo(() => {
    return detectSynthesisMode(askMutation.data?.answer_markdown ?? "");
  }, [askMutation.data?.answer_markdown]);

  const claimRefsByCitation = useMemo(() => {
    const refs = new Map<number, number[]>();
    for (const claim of claims) {
      for (const citationId of claim.citationIds) {
        const existing = refs.get(citationId) ?? [];
        refs.set(citationId, [...existing, claim.index]);
      }
    }
    return refs;
  }, [claims]);

  const activeClaimCitationIds = useMemo(() => {
    if (!activeClaim) {
      return new Set<number>();
    }
    return new Set(activeClaim.citationIds);
  }, [activeClaim]);

  const citationSourceOptions = useMemo(() => {
    const citations = askMutation.data?.citations ?? [];
    const sourceTypes = new Set<string>(citations.map((citation) => citation.source_type));
    return [
      { label: "All sources", value: "all" },
      ...[...sourceTypes].sort().map((sourceType) => ({
        label: sourceType,
        value: sourceType
      }))
    ];
  }, [askMutation.data?.citations]);

  const filteredCitations = useMemo(() => {
    const citations = askMutation.data?.citations ?? [];
    return sortAndFilterCitations(citations, {
      sortBy: citationSort,
      sourceType: citationSourceFilter,
      search: citationSearch,
      allowIds: onlyActiveClaimEvidence ? activeClaimCitationIds : null
    });
  }, [
    askMutation.data?.citations,
    citationSort,
    citationSourceFilter,
    citationSearch,
    onlyActiveClaimEvidence,
    activeClaimCitationIds
  ]);

  const citationCoverage = claims.length > 0 ? claims.filter((claim) => claim.citationIds.length > 0).length / claims.length : 0;
  const sourceTypeCoverage = getCitedSourceTypeCoverage(askMutation.data?.citations ?? []);

  const insufficientEvidence = useMemo(() => {
    const markdown = askMutation.data?.answer_markdown.toLowerCase() ?? "";
    return [
      "nemám dostatek důkazů",
      "nedostatek důkazů",
      "insufficient evidence",
      "not enough evidence"
    ].some((marker) => markdown.includes(marker));
  }, [askMutation.data?.answer_markdown]);

  const parsedProjectIds = useMemo(() => parseCsvIds(projectIds), [projectIds]);
  const parsedTrackerIds = useMemo(() => parseCsvIds(trackerIds), [trackerIds]);
  const parsedStatusIds = useMemo(() => parseCsvIds(statusIds), [statusIds]);

  const submitAsk = () => {
    const parsedTopK = Number.parseInt(topK, 10);
    askMutation.mutate({
      query,
      filters: {
        project_ids: parsedProjectIds,
        tracker_ids: parsedTrackerIds,
        status_ids: parsedStatusIds,
        from_date: fromDate ? `${fromDate}T00:00:00Z` : null,
        to_date: toDate ? `${toDate}T23:59:59Z` : null
      },
      top_k: Number.isFinite(parsedTopK) && parsedTopK > 0 ? parsedTopK : 5
    });

    const nextHistory = [
      {
        query,
        projectIds,
        trackerIds,
        statusIds,
        topK,
        fromDate,
        toDate,
        at: new Date().toISOString()
      },
      ...history
    ].slice(0, 12);
    setHistory(nextHistory);
    window.localStorage.setItem(HISTORY_KEY, JSON.stringify(nextHistory));
  };

  const onSelectCitation = (citationId: number) => {
    setActiveCitationId(citationId);
    const ownerClaim = claims.find((claim) => claim.citationIds.includes(citationId));
    if (ownerClaim) {
      setActiveClaimIndex(ownerClaim.index);
    }
  };

  const onSelectHistory = (item: AskHistoryItem) => {
    setQuery(item.query);
    setProjectIds(item.projectIds);
    setTrackerIds(item.trackerIds);
    setStatusIds(item.statusIds);
    setTopK(item.topK);
    setFromDate(item.fromDate);
    setToDate(item.toDate);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Ask Workbench and Citation Explorer"
        subtitle="Ask project questions, inspect grounded claims, and navigate evidence cards with source filters and debug diagnostics."
        actions={
          <Button variant="secondary" onClick={() => setDebugMode((previous) => !previous)}>
            {debugMode ? "Hide debug" : "Explain / debug"}
          </Button>
        }
      />

      <Card title="Question Workspace" description="Fine-tune filters for better retrieval precision.">
        <div className="mb-4 flex flex-wrap gap-2">
          {QUICK_PROMPTS.map((prompt) => (
            <Button key={prompt} variant="ghost" size="sm" onClick={() => setQuery(prompt)}>
              {prompt.slice(0, 54)}{prompt.length > 54 ? "…" : ""}
            </Button>
          ))}
        </div>

        <form
          className="space-y-4"
          onSubmit={(event) => {
            event.preventDefault();
            submitAsk();
          }}
        >
          <TextAreaField
            label="Question"
            name="query"
            rows={4}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <TextField
              label="Project IDs"
              name="projectIds"
              value={projectIds}
              onChange={(event) => setProjectIds(event.target.value)}
              hint="Comma-separated"
            />
            <TextField
              label="Tracker IDs"
              name="trackerIds"
              value={trackerIds}
              onChange={(event) => setTrackerIds(event.target.value)}
              hint="Comma-separated"
            />
            <TextField
              label="Status IDs"
              name="statusIds"
              value={statusIds}
              onChange={(event) => setStatusIds(event.target.value)}
              hint="Comma-separated"
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
            <TextField
              label="Top K"
              name="topK"
              value={topK}
              onChange={(event) => setTopK(event.target.value)}
              hint="1-30"
            />
          </div>

          <Button type="submit" disabled={askMutation.isPending || query.trim().length < 3}>
            {askMutation.isPending ? "Asking…" : "Run query"}
          </Button>
        </form>
      </Card>

      {askMutation.isError ? <ErrorState message={toUserMessage(askMutation.error)} /> : null}

      {askMutation.data ? (
        <section className="grid gap-4 xl:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
          <div className="space-y-4">
            <Card
              title="Answer"
              description={`Confidence ${(askMutation.data.confidence * 100).toFixed(0)}% · synthesis ${synthesisMode}`}
            >
              <MarkdownSurface
                markdown={askMutation.data.answer_markdown}
                activeCitationId={activeCitationId}
                activeClaimIndex={activeClaimIndex}
                onCitationClick={onSelectCitation}
              />
            </Card>

            <Card title="Grounding Indicators" description="Claim and evidence quality at a glance.">
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-xl bg-[var(--surface-1)] p-3">
                  <p className="text-xs uppercase tracking-wide text-[var(--ink-2)]">Claims</p>
                  <p className="text-2xl font-semibold text-[var(--ink-1)]">{claims.length}</p>
                </div>
                <div className="rounded-xl bg-[var(--surface-1)] p-3">
                  <p className="text-xs uppercase tracking-wide text-[var(--ink-2)]">Citation coverage</p>
                  <p className="text-2xl font-semibold text-[var(--ink-1)]">{(citationCoverage * 100).toFixed(0)}%</p>
                </div>
                <div className="rounded-xl bg-[var(--surface-1)] p-3">
                  <p className="text-xs uppercase tracking-wide text-[var(--ink-2)]">Used chunks</p>
                  <p className="text-2xl font-semibold text-[var(--ink-1)]">{askMutation.data.used_chunk_ids.length}</p>
                </div>
              </div>
              {insufficientEvidence ? (
                <p className="mt-3 rounded-xl bg-[var(--warning-soft)] px-3 py-2 text-sm text-[#7a4d10]">
                  Insufficient-evidence fallback detected. Try narrowing project/time filters or ask a more specific issue-level question.
                </p>
              ) : null}
            </Card>

            {claims.length > 0 ? (
              <Card title="Claim-to-Citation Mapping" description="Select claim to focus citation explorer.">
                <ul className="space-y-2">
                  {claims.map((claim) => {
                    const isActive = activeClaimIndex === claim.index;
                    return (
                      <li key={`claim-${claim.index}`}>
                        <button
                          type="button"
                          className={[
                            "w-full rounded-xl border px-3 py-2 text-left text-sm",
                            isActive
                              ? "border-[var(--brand)] bg-[var(--brand-soft)]/50"
                              : "border-[var(--border)] bg-[var(--surface-1)]"
                          ].join(" ")}
                          onClick={() => {
                            setActiveClaimIndex(claim.index);
                            setActiveCitationId(claim.citationIds[0] ?? null);
                          }}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-semibold text-[var(--ink-1)]">Claim {claim.index}</span>
                            <span className="text-xs text-[var(--ink-2)]">
                              citations {claim.citationIds.join(", ")}
                            </span>
                          </div>
                          <p className="mt-1 text-[var(--ink-1)]">{claim.text}</p>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </Card>
            ) : null}

            {debugMode ? (
              <Card title="Explain / Debug" description="Retrieval and synthesis diagnostics from response metadata.">
                <div className="grid gap-3 sm:grid-cols-2">
                  <p className="text-sm text-[var(--ink-1)]">
                    <strong>Retrieval mode:</strong> {retrievalDiagnostics.mode ?? "unknown"}
                  </p>
                  <p className="text-sm text-[var(--ink-1)]">
                    <strong>Synthesis mode:</strong> {synthesisMode}
                  </p>
                  <p className="text-sm text-[var(--ink-1)]">
                    <strong>Lexical candidates:</strong> {retrievalDiagnostics.lexical ?? "-"}
                  </p>
                  <p className="text-sm text-[var(--ink-1)]">
                    <strong>Vector candidates:</strong> {retrievalDiagnostics.vector ?? "-"}
                  </p>
                  <p className="text-sm text-[var(--ink-1)]">
                    <strong>Fused candidates:</strong> {retrievalDiagnostics.fused ?? "-"}
                  </p>
                  <p className="text-sm text-[var(--ink-1)]">
                    <strong>Cited source types:</strong>{" "}
                    {Object.entries(sourceTypeCoverage)
                      .map(([key, value]) => `${key}=${value}`)
                      .join(", ") || "-"}
                  </p>
                </div>
                <p className="mt-3 text-xs text-[var(--ink-2)]">
                  Used chunk IDs: {askMutation.data.used_chunk_ids.join(", ") || "-"}
                </p>
              </Card>
            ) : null}
          </div>

          <div className="space-y-3">
            <Card
              title="Citation Explorer"
              description={`Evidence cards: ${filteredCitations.length}/${askMutation.data.citations.length}`}
            >
              <div className="flex flex-wrap gap-2">
                <Button variant="secondary" size="sm" onClick={() => setCitationDrawerOpen((previous) => !previous)}>
                  {citationDrawerOpen ? "Hide explorer" : "Open explorer"}
                </Button>
                <label className="inline-flex items-center gap-2 rounded-xl border border-[var(--border)] px-3 py-2 text-sm text-[var(--ink-1)]">
                  <input
                    type="checkbox"
                    checked={onlyActiveClaimEvidence}
                    onChange={(event) => setOnlyActiveClaimEvidence(event.target.checked)}
                  />
                  Only active claim evidence
                </label>
              </div>

              {citationDrawerOpen ? (
                <div className="mt-4 space-y-4">
                  <div className="grid gap-3 sm:grid-cols-3">
                    <SelectField
                      label="Sort"
                      name="citationSort"
                      value={citationSort}
                      onChange={(event) => setCitationSort(event.target.value as CitationSort)}
                      options={[
                        { label: "ID ascending", value: "id_asc" },
                        { label: "Source type", value: "source_type" },
                        { label: "Snippet length", value: "snippet_length_desc" }
                      ]}
                    />
                    <SelectField
                      label="Source filter"
                      name="sourceFilter"
                      value={citationSourceFilter}
                      onChange={(event) => setCitationSourceFilter(event.target.value)}
                      options={citationSourceOptions}
                    />
                    <TextField
                      label="Search evidence"
                      name="citationSearch"
                      value={citationSearch}
                      onChange={(event) => setCitationSearch(event.target.value)}
                      placeholder="source, id, snippet..."
                    />
                  </div>

                  {filteredCitations.length === 0 ? (
                    <EmptyState
                      title="No citations matched filters"
                      description="Adjust source filter/search or disable active-claim-only mode."
                    />
                  ) : (
                    <div className="max-h-[65vh] space-y-3 overflow-y-auto pr-1">
                      {filteredCitations.map((citation: Citation) => (
                        <CitationCard
                          key={citation.id}
                          citation={citation}
                          isActive={activeCitationId === citation.id}
                          claimRefs={claimRefsByCitation.get(citation.id) ?? []}
                          onSelect={onSelectCitation}
                        />
                      ))}
                    </div>
                  )}
                </div>
              ) : null}
            </Card>
          </div>
        </section>
      ) : (
        <EmptyState
          title="No answer yet"
          description="Submit a query to render answer, claim mapping, and citation explorer."
        />
      )}

      <Card title="Recent Sessions" description="Recent ask runs are stored locally with filters and can be replayed.">
        {history.length === 0 ? (
          <p className="text-sm text-[var(--ink-2)]">No local history yet.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {history.map((item) => (
              <li key={`${item.at}-${item.query}`} className="rounded-xl bg-[var(--surface-2)] px-3 py-2">
                <button
                  className="w-full text-left text-[var(--ink-1)]"
                  onClick={() => onSelectHistory(item)}
                >
                  <strong className="text-[var(--ink-0)]">{item.query}</strong>
                  <br />
                  <span className="text-xs text-[var(--ink-2)]">
                    project={item.projectIds || "default"}, tracker={item.trackerIds || "-"}, status={item.statusIds || "-"}, topK={item.topK} · {new Date(item.at).toLocaleString()}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
