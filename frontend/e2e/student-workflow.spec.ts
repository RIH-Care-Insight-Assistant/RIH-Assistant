import { expect, test } from "@playwright/test";

// Synthetic student journey against the real backend. No real student data.

test("student asks, gets cited answers and safety guidance, clarifies, rates and resumes", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("note")).toContainText("not an official UMBC");

  // Grounded answer with sources.
  await page.getByRole("button", { name: "What are the RIH hours?" }).click();
  const sources = page.getByRole("region", { name: "Sources" }).first();
  await expect(sources).toBeVisible();
  await expect(sources.getByRole("link").first()).toHaveAttribute("href", /^https:\/\//);
  // Governed provenance is visible: C1 records are baseline sources awaiting review.
  await expect(sources.getByText("Baseline source, awaiting governed review").first()).toBeVisible();

  // Safety-first: deterministic guidance in a distinct alert, no sources.
  const input = page.getByLabel("Your message");
  await input.fill("I want to kill myself");
  await page.getByRole("button", { name: "Send" }).click();
  const alert = page.getByRole("alert").filter({ hasText: "988" });
  await expect(alert).toBeVisible();
  await expect(alert.getByRole("heading", { name: "Urgent safety guidance" })).toBeVisible();

  // Clarification with server-defined options.
  await input.fill("I need to make an appointment");
  await page.getByRole("button", { name: "Send" }).click();
  await page.getByRole("button", { name: "Medical appointment" }).click();
  await expect(page.getByText("I want to schedule a medical appointment")).toBeVisible();

  // Feedback.
  const helpful = page.getByRole("button", { name: "Helpful", exact: true }).last();
  await helpful.click();
  await expect(helpful).toHaveAttribute("aria-pressed", "true");

  // Continue the session after a reload: history comes from the server.
  await page.reload();
  const history = page.getByRole("navigation", { name: "Conversation history" });
  await history.getByRole("button", { name: "What are the RIH hours?", exact: true }).click();
  await expect(page.getByText("I want to schedule a medical appointment")).toBeVisible();
  await expect(page.getByRole("alert").filter({ hasText: "988" })).toBeVisible();
});

test("resources show provenance and the staff area is server-gated", async ({ page }) => {
  await page.goto("/#/resources");
  await expect(page.getByRole("heading", { name: "Campus resources" })).toBeVisible();
  await expect(page.locator(".resource").first()).toBeVisible();
  await page.getByLabel("Search resources").fill("billing");
  await page.getByRole("button", { name: "Search" }).click();
  await expect(page.getByRole("link", { name: "RIH Billing" })).toBeVisible();

  await page.getByRole("link", { name: "Staff" }).click();
  await expect(page.getByText(/requires a signed-in reviewer or administrator/)).toBeVisible();
  const direct = await page.request.get("/api/v1/admin/status");
  expect(direct.status()).toBe(403);
});
