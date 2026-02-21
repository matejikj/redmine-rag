import type { ReactNode } from "react";

interface Props {
  title: string;
  subtitle: string;
  actions?: ReactNode;
}

export function PageHeader({ title, subtitle, actions }: Props) {
  return (
    <section className="surface-card bg-[var(--surface-1)] p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="section-title text-3xl font-semibold text-[var(--ink-1)]">{title}</h2>
          <p className="mt-2 max-w-2xl text-sm text-[var(--ink-2)]">{subtitle}</p>
        </div>
        {actions ? <div>{actions}</div> : null}
      </div>
    </section>
  );
}
