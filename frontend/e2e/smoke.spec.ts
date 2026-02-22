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
  await expect(page.getByText("Redmine RAG")).toBeVisible();

  await page.getByRole("link", { name: "Sync" }).click();
  await expect(page.getByRole("heading", { name: "Sync and Ingestion Control Center" })).toBeVisible();
  await expect(page.getByText("Selected job: job-failed-seed")).toBeVisible();

  await page.getByRole("button", { name: "Start sync" }).click();
  await expect(page.getByText("Job accepted:")).toBeVisible();
  await expect(page.locator("p:has-text('Job accepted:') code")).toHaveText("job-new-sync");
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
        ].join("\n"),
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
  const retrievalModeParagraph = page.locator("p", {
    has: page.locator("strong", { hasText: "Retrieval mode:" })
  });
  await expect(retrievalModeParagraph).toContainText("hybrid");

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
  await expect(page.getByText(/^FAIL$/)).toBeVisible();

  await page.getByRole("button", { name: "Run extraction" }).click();
  await expect(page.getByText("processed 4 issues")).toBeVisible();
  await expect(page.getByText("success: 3")).toBeVisible();
});

test("ops dashboard run controls and release checklist journey", async ({ page }) => {
  const runs = [
    {
      id: "run-1",
      action: "backup",
      status: "success",
      started_at: "2026-02-21T12:00:00Z",
      finished_at: "2026-02-21T12:00:02Z",
      detail: "Backup completed at backups/snapshot-20260221T120000Z",
      summary: { backup_dir: "backups/snapshot-20260221T120000Z" }
    }
  ];

  await page.route("**/healthz", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "degraded",
        app: "redmine-rag",
        version: "0.1.0",
        utc_time: "2026-02-21T12:30:00Z",
        checks: [
          { name: "database", status: "ok", detail: "Database connection healthy", latency_ms: 5 },
          {
            name: "llm_telemetry",
            status: "warn",
            detail: JSON.stringify({
              success_rate: 0.93,
              p95_latency_ms: 12900,
              circuit: { state: "closed" }
            }),
            latency_ms: 12900
          }
        ],
        sync_jobs: { queued: 0, running: 0, finished: 5, failed: 1 }
      })
    });
  });

  await page.route("**/v1/ops/environment", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        generated_at: "2026-02-21T12:30:00Z",
        app: "redmine-rag",
        version: "0.1.0",
        app_env: "dev",
        redmine_base_url: "http://127.0.0.1:8081",
        redmine_allowed_hosts: ["127.0.0.1", "localhost"],
        llm_provider: "ollama",
        llm_model: "mistral:7b-instruct-v0.3-q4_K_M",
        llm_extract_enabled: true
      })
    });
  });

  await page.route("**/v1/ops/runs?**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: runs,
        total: runs.length
      })
    });
  });

  await page.route("**/v1/ops/backup", async (route) => {
    runs.unshift({
      id: "run-2",
      action: "backup",
      status: "success",
      started_at: "2026-02-21T12:31:00Z",
      finished_at: "2026-02-21T12:31:03Z",
      detail: "Backup completed at backups/snapshot-20260221T123100Z",
      summary: { backup_dir: "backups/snapshot-20260221T123100Z" }
    });
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ accepted: true, run: runs[0] })
    });
  });

  await page.route("**/v1/ops/maintenance", async (route) => {
    runs.unshift({
      id: "run-3",
      action: "maintenance",
      status: "success",
      started_at: "2026-02-21T12:31:10Z",
      finished_at: "2026-02-21T12:31:13Z",
      detail: "Maintenance completed in 120 ms",
      summary: { elapsed_ms: 120 }
    });
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ accepted: true, run: runs[0] })
    });
  });

  await page.goto("/ops");
  await expect(page.getByRole("heading", { name: "Ops, Release, and Hardening" })).toBeVisible();
  await expect(page.getByText("mistral:7b-instruct-v0.3-q4_K_M")).toBeVisible();
  await expect(page.getByText("success=93.0%, p95=12900 ms, circuit=closed")).toBeVisible();

  await page.getByRole("button", { name: "Run backup" }).click();
  await expect(page.getByText("Backup run success:")).toBeVisible();

  await page.getByRole("button", { name: "Run maintenance" }).click();
  await expect(page.getByText("Maintenance run success:")).toBeVisible();

  await page.getByRole("checkbox").first().check();
  await expect(page.getByText("Completed 1/6")).toBeVisible();
});
