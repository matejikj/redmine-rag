import { Button } from "../ui/Button";

interface Props {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = "Action failed",
  message,
  onRetry
}: Props) {
  return (
    <div className="surface-card border-[#edbbb8] bg-[var(--danger-soft)] p-5" role="alert">
      <h3 className="section-title text-lg font-semibold text-[var(--danger-ink)]">{title}</h3>
      <p className="mt-2 text-sm text-[var(--danger-ink)]">{message}</p>
      {onRetry ? (
        <div className="mt-4">
          <Button variant="secondary" onClick={onRetry}>
            Retry request
          </Button>
        </div>
      ) : null}
    </div>
  );
}
