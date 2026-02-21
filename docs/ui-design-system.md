# UI Design System (Task 16)

This project uses a token-driven UI foundation in `frontend/src/styles/tokens.css`.

## Design tokens

- Typography:
  - `--font sans`: Space Grotesk
  - `--font serif`: Literata
- Color:
  - `--bg-page`, `--bg-accent` for layered background atmosphere
  - `--surface-*` for cards and control surfaces
  - `--ink-*` for content hierarchy
  - `--brand`, `--brand-strong`, `--brand-soft`
  - `--warning-soft`, `--danger-soft`, `--success-soft`
- Spacing:
  - `--space-1` … `--space-10`
- Radius:
  - `--radius-md`, `--radius-lg`, `--radius-xl`

## Reusable primitives

- Form controls:
  - `TextField`
  - `SelectField`
  - `TextAreaField`
- Actions:
  - `Button` (`primary`, `secondary`, `ghost`, `danger`)
- Layout blocks:
  - `Card`
  - `PageHeader`
  - `AppShell`
- Data display:
  - `DataTable`
  - `JobStatusBadge`
  - `CitationCard`
  - `MarkdownSurface`

## Standard UI states

- `LoadingState`
- `EmptyState`
- `ErrorState`

State components are used by pages as default behavior for all API calls.

## Accessibility baseline

- Label-first form controls and `aria-invalid` for validation errors.
- Global `:focus-visible` ring token.
- Keyboard skip link (`Skip to main content`).
- Contrast-safe status colors for warn/error/success markers.

## API client and error handling

- Typed API layer in `frontend/src/lib/api/client.ts`.
- Centralized `ApiError` with actionable fallback messages.
- Query/mutation hooks in `frontend/src/lib/api/hooks.ts`.

## Component usage examples

See `frontend/src/pages/DesignSystemPage.tsx` for canonical examples.

## Ask Usability Prompts (Task 18)

Use these realistic support questions during manual UX checks:

1. `What is the login callback issue and rollback plan?`
2. `Which issue documents incident triage for OAuth failures?`
3. `What evidence points to root cause and mitigation steps?`
4. `Summarize user impact and next actions for the latest auth incident.`
5. `What changed between initial incident and final resolution?`

## Metrics Dashboard Usage (Task 19)

Use this operator flow for terminal-free quality checks:

1. Open `Metrics` page.
2. Set `project_ids` and optional date window, then `Apply filters`.
3. Review global KPIs and `Per-Project Breakdown`.
4. Trigger `Run extraction` (optional issue scope) and verify latest counters:
   - `success`, `failed`, `skipped`, `retries`
5. Inspect `Evaluation and Regression Gate`:
   - gate status (`PASS`/`FAIL`/`MISSING`)
   - metric deltas against baseline
   - failure notes and artifact hints
6. Export snapshots for handover or incident notes.

## Ops Dashboard Usage (Task 20)

1. Open `Ops` page and review environment/runtime cards.
2. Use `Operations Controls` to run backup and maintenance actions.
3. Validate execution outcome in `Operations Run History`.
4. Filter `Health Checks` by `warn`/`fail` during incidents.
5. Complete `Release Readiness Checklist` before deployment cutover.
