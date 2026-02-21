import type { Citation } from "../../lib/api/types";

interface Props {
  citation: Citation;
  isActive?: boolean;
  claimRefs?: number[];
  onSelect?: (citationId: number) => void;
}

export function CitationCard({
  citation,
  isActive = false,
  claimRefs = [],
  onSelect
}: Props) {
  return (
    <article
      className={[
        "surface-card space-y-3 p-4",
        isActive ? "border-[var(--brand)] bg-[var(--brand-soft)]/40" : ""
      ].join(" ")}
    >
      <header className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-[var(--ink-2)]">
          <span className="rounded-full bg-[var(--surface-2)] px-2 py-1 font-semibold">#{citation.id}</span>
          <span>{citation.source_type}</span>
          <span className="rounded-full bg-[var(--brand-soft)] px-2 py-1 text-[var(--brand-strong)]">
            {citation.source_id}
          </span>
          {claimRefs.length > 0 ? (
            <span className="rounded-full bg-[var(--warning-soft)] px-2 py-1 text-[#7a4d10]">
              claims {claimRefs.join(", ")}
            </span>
          ) : null}
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="text-xs font-semibold text-[var(--ink-1)] underline decoration-[var(--border)] decoration-2 underline-offset-2"
            onClick={() => onSelect?.(citation.id)}
          >
            Focus
          </button>
          <a
            href={citation.url}
            target="_blank"
            rel="noreferrer"
            className="text-xs font-semibold text-[var(--brand-strong)] underline decoration-[var(--brand)] decoration-2 underline-offset-2"
          >
            Open source
          </a>
        </div>
      </header>
      <p className="text-sm leading-relaxed text-[var(--ink-1)]">{citation.snippet}</p>
    </article>
  );
}
