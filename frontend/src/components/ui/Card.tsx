import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "../../lib/utils/cn";

interface CardProps extends HTMLAttributes<HTMLElement> {
  title?: ReactNode;
  description?: ReactNode;
}

export function Card({ title, description, children, className, ...props }: CardProps) {
  return (
    <section className={cn("surface-card p-5", className)} {...props}>
      {(title || description) && (
        <header className="mb-4 space-y-1">
          {title ? <h3 className="section-title text-xl font-semibold leading-tight">{title}</h3> : null}
          {description ? <p className="text-sm text-[var(--ink-2)]">{description}</p> : null}
        </header>
      )}
      {children}
    </section>
  );
}
