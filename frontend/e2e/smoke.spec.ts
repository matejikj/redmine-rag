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
