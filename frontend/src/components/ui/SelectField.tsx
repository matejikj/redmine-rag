import type { SelectHTMLAttributes } from "react";

import { cn } from "../../lib/utils/cn";

interface Option {
  label: string;
  value: string;
}

interface Props extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  options: Option[];
  error?: string;
}

export function SelectField({ id, label, options, error, className, ...props }: Props) {
  const selectId = id ?? props.name;
  return (
    <div className="space-y-1">
      <label htmlFor={selectId} className="text-sm font-medium text-[var(--ink-1)]">
        {label}
      </label>
      <select
        id={selectId}
        className={cn(
          "h-10 w-full rounded-xl border bg-[var(--surface-0)] px-3 text-sm text-[var(--ink-0)]",
          error ? "border-[#c23f3b]" : "border-[var(--border)]",
          className
        )}
        aria-invalid={Boolean(error)}
        {...props}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error ? <p className="text-xs text-[var(--danger-ink)]">{error}</p> : null}
    </div>
  );
}
