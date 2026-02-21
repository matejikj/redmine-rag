import { expect, test } from "@playwright/test";

test("routing and API connectivity smoke", async ({ page }) => {
  const jobs = [
    {
      id: "job-failed-seed",
      status: "failed",
      payload: { project_ids: [1], modules: ["issues"], error_type: "ConnectError" },
      started_at: "2026-02-21T10:00:00Z",
      finished_at: "2026-02-21T10:00:25Z",
      error_message: "network timeout",
      created_at: "2026-02-21T10:00:00Z",
      updated_at: "2026-02-21T10:00:25Z"
    }
  ];

  await page.route("**/healthz", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "ok",
        app: "redmine-rag",
        version: "0.1.0",
        utc_time: "2026-02-21T00:00:00Z",
        checks: [],
        sync_jobs: { queued: 1, running: 0, finished: 3, failed: 0 }
      })
    });
  });

  await page.route("**/v1/sync/jobs?**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: jobs,
        total: jobs.length,
        counts: {
          queued: jobs.filter((job) => job.status === "queued").length,
          running: jobs.filter((job) => job.status === "running").length,
          finished: jobs.filter((job) => job.status === "finished").length,
          failed: jobs.filter((job) => job.status === "failed").length
        }
      })
    });
  });

  await page.route("**/v1/sync/jobs/*", async (route) => {
    const url = new URL(route.request().url());
    const jobId = url.pathname.split("/").at(-1);
    const job = jobs.find((item) => item.id === jobId);
    if (!job) {
      await route.fulfill({ status: 404, contentType: "application/json", body: "{\"detail\":\"not found\"}" });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(job)
    });
  });

  await page.route("**/v1/sync/redmine", async (route) => {
    jobs.unshift({
      id: "job-new-sync",
      status: "queued",
      payload: { project_ids: [1], modules: ["projects", "issues"] },
      started_at: null,
      finished_at: null,
      error_message: null,
      created_at: "2026-02-21T11:00:00Z",
      updated_at: "2026-02-21T11:00:00Z"
    });
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ job_id: "job-new-sync", accepted: true, detail: "Sync job queued" })
    });
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Platform Control Plane" })).toBeVisible();
  await expect(page.getByText("redmine-rag")).toBeVisible();

  await page.getByRole("link", { name: "Sync" }).click();
  await expect(page.getByRole("heading", { name: "Sync and Ingestion Control Center" })).toBeVisible();
  await expect(page.getByText("Selected job: job-failed-seed")).toBeVisible();

  await page.getByRole("button", { name: "Start sync" }).click();
  await expect(page.getByText("Job accepted:")).toBeVisible();
  await expect(page.getByText("job-new-sync")).toBeVisible();
});

test("ask workbench and citation explorer journey", async ({ page }) => {
  await page.route("**/v1/ask", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        answer_markdown: [
          "### Odpověď podložená Redmine zdroji (LLM)",
          "1. OAuth callback timeout affects Safari login flow. [1, 2]",
          "2. Rollback guidance is documented in incident playbook. [2]",
          "",
          "_Retrieval mode: hybrid; lexical=10, vector=7, fused=5_"
        ].join("\\n"),
        citations: [
          {
            id: 1,
            url: "https://redmine.example.com/issues/501",
            source_type: "issue",
            source_id: "501",
            snippet: "OAuth callback timeout impacts Safari users."
          },
          {
            id: 2,
            url: "https://redmine.example.com/wiki/Incident-Triage-Playbook",
            source_type: "wiki",
            source_id: "1:Incident-Triage-Playbook",
            snippet: "Rollback checklist and communication steps."
          }
        ],
        used_chunk_ids: [1001, 1002],
        confidence: 0.82
      })
    });
  });

  await page.goto("/ask");
  await expect(page.getByRole("heading", { name: "Ask Workbench and Citation Explorer" })).toBeVisible();

  await page.getByRole("button", { name: "Run query" }).click();
  await expect(page.getByText("Claim-to-Citation Mapping")).toBeVisible();
  await expect(page.getByRole("button", { name: "[1]" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Explain / debug" })).toBeVisible();

  await page.getByRole("button", { name: "Explain / debug" }).click();
  await expect(page.getByText("Retrieval mode:")).toBeVisible();
  await expect(page.getByText("hybrid")).toBeVisible();

  await page.getByLabel("Source filter").selectOption("wiki");
  await expect(page.getByText("1:Incident-Triage-Playbook")).toBeVisible();
});

test("metrics dashboard extraction and evaluation flow", async ({ page }) => {
  await page.route("**/v1/metrics/summary?**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        generated_at: "2026-02-21T11:12:00Z",
        from_date: "2026-02-01T00:00:00Z",
        to_date: "2026-02-21T23:59:59Z",
        project_ids: [1],
        extractor_version: "det-v1",
        issues_total: 12,
        issues_with_first_response: 10,
        issues_with_resolution: 8,
        avg_first_response_s: 420,
        avg_resolution_s: 8400,
        reopen_total: 3,
        touch_total: 49,
        handoff_total: 11,
        by_project: [
          {
            project_id: 1,
            issues_total: 12,
            issues_with_first_response: 10,
            issues_with_resolution: 8,
            avg_first_response_s: 420,
            avg_resolution_s: 8400,
            reopen_total: 3,
            touch_total: 49,
            handoff_total: 11
          }
        ]
      })
    });
  });

  await page.route("**/v1/evals/latest", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        generated_at: "2026-02-21T11:12:30Z",
        status: "fail",
        current_report_path: "evals/reports/latest_eval_report.json",
        baseline_path: "evals/baseline_metrics.v1.json",
        regression_gate_path: "evals/reports/latest_regression_gate.json",
        current_metrics: {
          query_count: 50,
          citation_coverage: 0.96,
          groundedness: 0.98,
          retrieval_hit_rate: 0.97,
          source_type_coverage: { issue: 45 }
        },
        baseline_metrics: {
          query_count: 50,
          citation_coverage: 1.0,
          groundedness: 1.0,
          retrieval_hit_rate: 1.0,
          source_type_coverage: { issue: 44 }
        },
        comparisons: [
          {
            metric: "citation_coverage",
            baseline: 1.0,
            current: 0.96,
            delta: -0.04,
            allowed_drop: 0.01,
            passed: false
          }
        ],
        failures: ["citation_coverage dropped below threshold"],
        llm_runtime_failures: [],
        notes: []
      })
    });
  });

  await page.route("**/v1/extract/properties", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        accepted: true,
        processed_issues: 4,
        detail: "Deterministic extraction completed. LLM ok=3, failed=1, skipped=0, retries=2."
      })
    });
  });

  await page.goto("/metrics");
  await expect(
    page.getByRole("heading", { name: "Metrics, Extraction, and Evaluation Dashboard" })
  ).toBeVisible();
  await expect(page.getByText("Per-Project Breakdown")).toBeVisible();
  await expect(page.getByText("Gate status:")).toBeVisible();
  await expect(page.getByText("FAIL")).toBeVisible();

  await page.getByRole("button", { name: "Run extraction" }).click();
  await expect(page.getByText("processed 4 issues")).toBeVisible();
  await expect(page.getByText("success: 3")).toBeVisible();
});
