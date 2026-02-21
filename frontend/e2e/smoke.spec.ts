import { expect, test } from "@playwright/test";

test("routing and API connectivity smoke", async ({ page }) => {
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
        items: [],
        total: 0,
        counts: { queued: 0, running: 0, finished: 0, failed: 0 }
      })
    });
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Platform Control Plane" })).toBeVisible();
  await expect(page.getByText("redmine-rag")).toBeVisible();

  await page.getByRole("link", { name: "Sync" }).click();
  await expect(page.getByRole("heading", { name: "Sync and Ingestion" })).toBeVisible();
});
