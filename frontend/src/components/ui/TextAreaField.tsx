import type { TextareaHTMLAttributes } from "react";

import { cn } from "../../lib/utils/cn";

interface Props extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  error?: string;
  hint?: string;
}

export function TextAreaField({ id, label, error, hint, className, ...props }: Props) {
  const areaId = id ?? props.name;
  return (
    <div className="space-y-1">
      <label htmlFor={areaId} className="text-sm font-medium text-[var(--ink-1)]">
        {label}
      </label>
      <textarea
        id={areaId}
        className={cn(
          "w-full rounded-xl border bg-[var(--surface-0)] px-3 py-2 text-sm text-[var(--ink-0)]",
          error ? "border-[#c23f3b]" : "border-[var(--border)]",
          className
        )}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${areaId}-error` : hint ? `${areaId}-hint` : undefined}
        {...props}
      />
      {hint && !error ? (
        <p id={`${areaId}-hint`} className="text-xs text-[var(--ink-2)]">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={`${areaId}-error`} className="text-xs text-[var(--danger-ink)]">
          {error}
        </p>
      ) : null}
    </div>
  );
}
