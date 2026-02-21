import type { InputHTMLAttributes } from "react";

import { cn } from "../../lib/utils/cn";

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  hint?: string;
}

export function TextField({ id, label, error, hint, className, ...props }: Props) {
  const inputId = id ?? props.name;
  return (
    <div className="space-y-1">
      <label htmlFor={inputId} className="text-sm font-medium text-[var(--ink-1)]">
        {label}
      </label>
      <input
        id={inputId}
        className={cn(
          "h-10 w-full rounded-xl border bg-[var(--surface-0)] px-3 text-sm text-[var(--ink-0)]",
          error ? "border-[#c23f3b]" : "border-[var(--border)]",
          className
        )}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
        {...props}
      />
      {hint && !error ? (
        <p id={`${inputId}-hint`} className="text-xs text-[var(--ink-2)]">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={`${inputId}-error`} className="text-xs text-[var(--danger-ink)]">
          {error}
        </p>
      ) : null}
    </div>
  );
}
