interface Props {
  markdown: string;
  activeCitationId?: number | null;
  onCitationClick?: (citationId: number) => void;
  activeClaimIndex?: number | null;
}

const CLAIM_LINE_PATTERN = /^(\d+)\.\s(.+?)\s\[(\d+(?:,\s*\d+)*)\]$/;

export function MarkdownSurface({
  markdown,
  activeCitationId = null,
  onCitationClick,
  activeClaimIndex = null
}: Props) {
  const lines = markdown.split("\n");

  return (
    <div className="surface-card p-5">
      {lines.map((line, index) => {
        const trimmed = line.trim();
        if (trimmed.length === 0) {
          return <div key={`line-${index}`} className="h-3" />;
        }

        if (trimmed.startsWith("### ")) {
          return (
            <h3 key={`line-${index}`} className="section-title mt-2 text-lg font-semibold">
              {trimmed.slice(4)}
            </h3>
          );
        }

        const claimMatched = trimmed.match(CLAIM_LINE_PATTERN);
        if (claimMatched) {
          const claimIndex = Number.parseInt(claimMatched[1], 10);
          const claimText = claimMatched[2];
          const citationIds = claimMatched[3]
            .split(",")
            .map((item) => Number.parseInt(item.trim(), 10))
            .filter((item) => Number.isFinite(item) && item > 0);

          const claimIsActive = activeClaimIndex === claimIndex;
          return (
            <div
              key={`line-${index}`}
              className={[
                "my-1 rounded-xl border px-3 py-2 text-sm leading-relaxed",
                claimIsActive
                  ? "border-[var(--brand)] bg-[var(--brand-soft)]/40 text-[var(--ink-0)]"
                  : "border-[var(--border)] bg-[var(--surface-1)] text-[var(--ink-0)]"
              ].join(" ")}
            >
              <p>
                <span className="font-semibold">{claimIndex}.</span> {claimText}
              </p>
              <div className="mt-1 flex flex-wrap items-center gap-1 text-xs">
                <span className="text-[var(--ink-2)]">Citations:</span>
                {citationIds.map((citationId) => (
                  <button
                    key={`citation-marker-${claimIndex}-${citationId}`}
                    type="button"
                    onClick={() => onCitationClick?.(citationId)}
                    className={[
                      "rounded-full border px-2 py-0.5 font-semibold",
                      activeCitationId === citationId
                        ? "border-[var(--brand)] bg-[var(--brand-soft)] text-[var(--brand-strong)]"
                        : "border-[var(--border)] bg-white text-[var(--ink-1)]"
                    ].join(" ")}
                  >
                    [{citationId}]
                  </button>
                ))}
              </div>
            </div>
          );
        }

        if (/^\d+\.\s/.test(trimmed)) {
          return (
            <p key={`line-${index}`} className="my-1 text-sm leading-relaxed text-[var(--ink-0)]">
              {trimmed}
            </p>
          );
        }

        return (
          <p key={`line-${index}`} className="my-1 text-sm leading-relaxed text-[var(--ink-1)]">
            {trimmed}
          </p>
        );
      })}
    </div>
  );
}
