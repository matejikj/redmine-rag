import type { Citation } from "../../lib/api/types";

interface Props {
  citation: Citation;
}

export function CitationCard({ citation }: Props) {
  return (
    <article className="surface-card space-y-3 p-4">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-[var(--ink-2)]">
          <span className="rounded-full bg-[var(--surface-2)] px-2 py-1 font-semibold">#{citation.id}</span>
          <span>{citation.source_type}</span>
          <span className="rounded-full bg-[var(--brand-soft)] px-2 py-1 text-[var(--brand-strong)]">
            {citation.source_id}
          </span>
        </div>
        <a
          href={citation.url}
          target="_blank"
          rel="noreferrer"
          className="text-xs font-semibold text-[var(--brand-strong)] underline decoration-[var(--brand)] decoration-2 underline-offset-2"
        >
          Open source
        </a>
      </header>
      <p className="text-sm leading-relaxed text-[var(--ink-1)]">{citation.snippet}</p>
    </article>
  );
}
