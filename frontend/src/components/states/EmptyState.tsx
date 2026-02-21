interface Props {
  title: string;
  description: string;
}

export function EmptyState({ title, description }: Props) {
  return (
    <div className="surface-card p-5">
      <h3 className="section-title text-lg font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-[var(--ink-2)]">{description}</p>
    </div>
  );
}
