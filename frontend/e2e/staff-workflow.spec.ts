import { expect, test, type Page } from "@playwright/test";

// Synthetic staff accounts created by scripts/dev/e2e_backend.py for this run only.
const PASSWORD = process.env.RIH_E2E_STAFF_PASSWORD ?? "";

async function signIn(page: Page, username: string) {
  await page.goto("/#/staff");
  await page.getByLabel("Username").fill(username);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByText(`Signed in as ${username}`)).toBeVisible();
}

test("reviewer rejects a source and students no longer get it cited", async ({ page }) => {
  expect(PASSWORD.length).toBeGreaterThan(12);
  await signIn(page, "e2e.reviewer");
  const tabs = page.getByRole("tablist", { name: "Staff sections" });
  await expect(tabs.getByRole("tab")).toHaveText(["Sources", "Governance", "Feedback"]);
  await page.getByRole("button", { name: "Reject RIH Billing" }).click();
  await expect(page.getByRole("row", { name: /RIH Billing/ })).toContainText("rejected");

  // The reviewer's server-side session cannot reach admin-only data.
  expect((await page.request.get("/api/v1/admin/users")).status()).toBe(403);

  await page.goto("/#/chat");
  await page.getByLabel("Your message").fill("Who do I contact about billing?");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("Here's what I found:").last()).toBeVisible();
  await expect(page.getByRole("link", { name: "RIH Billing" })).toHaveCount(0);
});

test("reviewer sees the governance dashboard and readiness is not approvable", async ({ page }) => {
  await signIn(page, "e2e.reviewer");
  await page.getByRole("tab", { name: "Governance" }).click();
  await expect(page.getByRole("heading", { name: /Release readiness:/ })).toBeVisible();
  await expect(page.getByRole("table")).toContainText("R-01");
  await page.getByLabel("Risk", { exact: true }).selectOption("R-05");
  await page.getByLabel("Decision", { exact: true }).selectOption("confirm_assessment");
  await page.getByLabel("Rationale").fill("Synthetic E2E review: assessment matches the stale baseline sources.");
  await page.getByRole("button", { name: "Record review" }).click();
  await expect(page.getByRole("row", { name: /R-05/ })).toContainText("confirm_assessment by e2e.reviewer");
  await expect(page.getByRole("heading", { name: "Release decision (admin)" })).toHaveCount(0);
});

test("admin sees the audit log with denied and allowed decisions", async ({ page }) => {
  await signIn(page, "e2e.admin");
  await page.getByRole("tab", { name: "Audit log" }).click();
  const table = page.getByRole("table");
  await expect(table).toContainText("tool:retrieve_resources");
  await expect(table).toContainText("denied");
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByRole("heading", { name: "Staff sign-in" })).toBeVisible();
  expect((await page.request.get("/api/v1/admin/audit")).status()).toBe(401);
});
