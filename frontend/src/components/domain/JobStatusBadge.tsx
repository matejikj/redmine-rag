import { cn } from "../../lib/utils/cn";

interface Props {
  status: string;
}

const statusClass: Record<string, string> = {
  queued: "bg-[var(--surface-2)] text-[var(--ink-1)] border-[var(--border)]",
  running: "bg-[var(--warning-soft)] text-[#7a4d10] border-[#f0d4a7]",
  finished: "bg-[var(--success-soft)] text-[#1d5f1f] border-[#b7dfb4]",
  failed: "bg-[var(--danger-soft)] text-[var(--danger-ink)] border-[#edbbb8]"
};

export function JobStatusBadge({ status }: Props) {
  const normalized = status.trim().toLowerCase();
  return (
    <span
      className={cn(
        "inline-flex rounded-full border px-2 py-0.5 text-xs font-semibold uppercase tracking-wide",
        statusClass[normalized] ?? "bg-[var(--surface-2)] text-[var(--ink-1)] border-[var(--border)]"
      )}
    >
      {status}
    </span>
  );
}
