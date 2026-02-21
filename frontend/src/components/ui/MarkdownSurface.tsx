interface Props {
  markdown: string;
}

export function MarkdownSurface({ markdown }: Props) {
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
