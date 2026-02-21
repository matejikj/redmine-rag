import { CitationCard } from "../components/domain/CitationCard";
import { JobStatusBadge } from "../components/domain/JobStatusBadge";
import { PageHeader } from "../components/layout/PageHeader";
import { EmptyState } from "../components/states/EmptyState";
import { ErrorState } from "../components/states/ErrorState";
import { LoadingState } from "../components/states/LoadingState";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { SelectField } from "../components/ui/SelectField";
import { TextAreaField } from "../components/ui/TextAreaField";
import { TextField } from "../components/ui/TextField";

export function DesignSystemPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Design System"
        subtitle="Tokens, reusable primitives and state components for consistent feature pages."
      />

      <section className="grid gap-4 md:grid-cols-2">
        <Card title="Buttons" description="Primary, secondary, ghost and danger variants.">
          <div className="flex flex-wrap gap-2">
            <Button>Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="danger">Danger</Button>
          </div>
        </Card>

        <Card title="Status badges" description="Reusable status marker for jobs and checks.">
          <div className="flex flex-wrap gap-2">
            <JobStatusBadge status="queued" />
            <JobStatusBadge status="running" />
            <JobStatusBadge status="finished" />
            <JobStatusBadge status="failed" />
          </div>
        </Card>
      </section>

      <Card title="Form primitives" description="Label-first accessible controls with inline hints/errors.">
        <div className="grid gap-3 md:grid-cols-2">
          <TextField label="Project IDs" name="projectIdsPreview" defaultValue="1,2" hint="Comma-separated" />
          <SelectField
            label="Status"
            name="statusPreview"
            defaultValue="running"
            options={[
              { label: "Queued", value: "queued" },
              { label: "Running", value: "running" },
              { label: "Finished", value: "finished" }
            ]}
          />
          <div className="md:col-span-2">
            <TextAreaField
              label="Question"
              name="queryPreview"
              defaultValue="What changed in yesterday's rollback incident?"
              rows={3}
            />
          </div>
        </div>
      </Card>

      <section className="grid gap-4 md:grid-cols-3">
        <LoadingState label="Loading preview" />
        <EmptyState title="Empty state" description="Use when dataset is valid but currently empty." />
        <ErrorState message="Use for actionable API failure messaging." />
      </section>

      <CitationCard
        citation={{
          id: 4,
          url: "https://redmine.example.com/issues/501",
          source_type: "issue",
          source_id: "501",
          snippet: "OAuth callback timeout impacts Safari users; rollback playbook requires comms update."
        }}
      />
    </div>
  );
}
