import { useEffect, useMemo, useState } from "react";

import { CitationCard } from "../components/domain/CitationCard";
import { PageHeader } from "../components/layout/PageHeader";
import { EmptyState } from "../components/states/EmptyState";
import { ErrorState } from "../components/states/ErrorState";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { MarkdownSurface } from "../components/ui/MarkdownSurface";
import { TextAreaField } from "../components/ui/TextAreaField";
import { TextField } from "../components/ui/TextField";
import { useAskMutation } from "../lib/api/hooks";
import { toUserMessage } from "../lib/utils/errors";

interface AskHistoryItem {
  query: string;
  at: string;
}

const HISTORY_KEY = "redmine-rag.ask-history";

export function AskPage() {
  const [query, setQuery] = useState("What is the login callback issue and rollback plan?");
  const [projectIds, setProjectIds] = useState("1");
  const [topK, setTopK] = useState("5");
  const [history, setHistory] = useState<AskHistoryItem[]>([]);

  const askMutation = useAskMutation();

  useEffect(() => {
    const raw = window.localStorage.getItem(HISTORY_KEY);
    if (!raw) {
      return;
    }
    try {
      const parsed = JSON.parse(raw) as AskHistoryItem[];
      setHistory(parsed.slice(0, 10));
    } catch {
      setHistory([]);
    }
  }, []);

  const citationCount = askMutation.data?.citations.length ?? 0;
  const usedChunkCount = askMutation.data?.used_chunk_ids.length ?? 0;

  const parsedProjectIds = useMemo(
    () =>
      projectIds
        .split(",")
        .map((item) => Number.parseInt(item.trim(), 10))
        .filter((item) => Number.isFinite(item) && item > 0),
    [projectIds]
  );

  const submitAsk = () => {
    const parsedTopK = Number.parseInt(topK, 10);
    askMutation.mutate({
      query,
      filters: {
        project_ids: parsedProjectIds,
        tracker_ids: [],
        status_ids: [],
        from_date: null,
        to_date: null
      },
      top_k: Number.isFinite(parsedTopK) && parsedTopK > 0 ? parsedTopK : 5
    });

    const nextHistory = [{ query, at: new Date().toISOString() }, ...history].slice(0, 10);
    setHistory(nextHistory);
    window.localStorage.setItem(HISTORY_KEY, JSON.stringify(nextHistory));
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Ask Workbench"
        subtitle="Query the platform and inspect grounding with citation cards. Response rendering intentionally preserves claim markers."
      />

      <Card title="Question Input" description="Use precise project-scoped questions for stronger grounding.">
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
          <div className="grid gap-4 sm:grid-cols-2">
            <TextField
              label="Project IDs"
              name="projectIds"
              value={projectIds}
              onChange={(event) => setProjectIds(event.target.value)}
              hint="Comma-separated IDs"
            />
            <TextField
              label="Top K"
              name="topK"
              value={topK}
              onChange={(event) => setTopK(event.target.value)}
              hint="How many chunks to retrieve"
            />
          </div>
          <Button type="submit" disabled={askMutation.isPending || query.trim().length < 3}>
            {askMutation.isPending ? "Asking…" : "Run query"}
          </Button>
        </form>
      </Card>

      {askMutation.isError ? <ErrorState message={toUserMessage(askMutation.error)} /> : null}

      {askMutation.data ? (
        <section className="grid gap-4 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
          <div className="space-y-4">
            <Card title="Answer" description={`Confidence: ${askMutation.data.confidence.toFixed(2)}`}>
              <MarkdownSurface markdown={askMutation.data.answer_markdown} />
            </Card>
            <Card title="Grounding Summary" description="Fast visibility for quality checks.">
              <p className="text-sm text-[var(--ink-1)]">
                Citations: <strong>{citationCount}</strong> | Used chunks: <strong>{usedChunkCount}</strong>
              </p>
            </Card>
          </div>
          <div className="space-y-3">
            <h3 className="section-title text-xl font-semibold">Citations</h3>
            {askMutation.data.citations.length === 0 ? (
              <EmptyState
                title="No evidence returned"
                description="Either retrieval found no usable chunks or the query needs tighter filters."
              />
            ) : (
              askMutation.data.citations.map((citation) => (
                <CitationCard key={citation.id} citation={citation} />
              ))
            )}
          </div>
        </section>
      ) : (
        <EmptyState
          title="No answer yet"
          description="Submit your first question to render answer and evidence panels."
        />
      )}

      <Card title="Recent Questions" description="Stored locally in browser for quick repeat queries.">
        {history.length === 0 ? (
          <p className="text-sm text-[var(--ink-2)]">No local history yet.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {history.map((item) => (
              <li key={`${item.at}-${item.query}`} className="rounded-xl bg-[var(--surface-2)] px-3 py-2">
                <button
                  className="w-full text-left text-[var(--ink-1)]"
                  onClick={() => setQuery(item.query)}
                >
                  <strong className="text-[var(--ink-0)]">{item.query}</strong>
                  <br />
                  <span className="text-xs text-[var(--ink-2)]">
                    {new Date(item.at).toLocaleString()}
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
