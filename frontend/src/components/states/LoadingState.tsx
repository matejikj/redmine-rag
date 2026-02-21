interface Props {
  label?: string;
}

export function LoadingState({ label = "Loading data" }: Props) {
  return (
    <div
      className="surface-card flex items-center gap-3 p-4 text-sm text-[var(--ink-1)]"
      role="status"
      aria-live="polite"
    >
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-[var(--border)] border-t-[var(--brand)]" />
      <span>{label}…</span>
    </div>
  );
}
