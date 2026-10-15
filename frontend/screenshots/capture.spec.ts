import { mkdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { expect, test, type Page } from "@playwright/test";

// Captures the README screenshots from the running application (playwright.screenshots.config.ts).
// Every screen is reached through the real UI and API with synthetic messages and throwaway
// demo staff accounts; passwords are typed into the form but never on screen when a capture runs.

const OUT = fileURLToPath(new URL("../../docs/assets/screenshots", import.meta.url));
const PASSWORD = process.env.RIH_E2E_STAFF_PASSWORD ?? "";
const captured: string[] = [];
mkdirSync(OUT, { recursive: true });

async function settle(page: Page) {
  await page.waitForLoadState("networkidle");
  await page.evaluate(async () => {
    await document.fonts.ready;
    (document.activeElement as HTMLElement | null)?.blur(); // no focus ring or caret in the image
  });
  await page.mouse.move(0, 0);
}

async function shot(page: Page, name: string, fullPage = false) {
  await settle(page);
  await page.screenshot({ path: `${OUT}/${name}.png`, animations: "disabled", caret: "hide", fullPage });
  captured.push(name);
}

async function shotOf(page: Page, selector: string, name: string) {
  await settle(page);
  await page.locator(selector).first().screenshot({ path: `${OUT}/${name}.png`, animations: "disabled", caret: "hide" });
  captured.push(name);
}

// The app scrolls new answers into view; for a capture, start at a question (the latest by default).
async function showQuestion(page: Page, which: "first" | "last" = "last") {
  await page.evaluate((pick) => {
    const body = document.querySelector(".chat__body") as HTMLElement | null;
    const asks = document.querySelectorAll(".msg--user");
    const last = asks[pick === "first" ? 0 : asks.length - 1] as HTMLElement | undefined;
    if (body && last) body.scrollTop += last.getBoundingClientRect().top - body.getBoundingClientRect().top - 16;
  }, which);
}

async function ask(page: Page, text: string) {
  const answers = page.locator(".msg--assistant");
  const before = await answers.count();
  await page.getByLabel("Your message").fill(text);
  await page.getByRole("button", { name: "Send" }).click();
  await expect(answers).toHaveCount(before + 1);
}

async function signIn(page: Page, username: string) {
  await page.goto("/#/staff");
  await page.getByLabel("Username").fill(username);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByText(`Signed in as ${username}`)).toBeVisible();
}

test.describe.configure({ mode: "serial" });

test("student chat: welcome, cited answer and safety guidance", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /How can I help/ })).toBeVisible();
  await shot(page, "chat-welcome");

  await page.getByRole("button", { name: "What are the RIH hours?" }).click();
  await expect(page.getByRole("region", { name: "Sources" }).first()).toBeVisible();
  await page.getByRole("button", { name: "Helpful", exact: true }).last().click();
  await showQuestion(page);
  await shot(page, "chat-answer-citations");

  // Synthetic crisis message: deterministic routing returns fixed guidance with no sources.
  await ask(page, "I have been thinking about ending my life");
  await expect(page.getByRole("heading", { name: "Urgent safety guidance" })).toBeVisible();
  await showQuestion(page);
  await shot(page, "chat-safety-guidance");
});

test("conversation history and clarification", async ({ page }) => {
  await page.goto("/");
  await ask(page, "How do I submit immunization records?");
  await page.getByRole("button", { name: "New conversation" }).click();
  await ask(page, "Who do I contact about billing?");
  await page.getByRole("button", { name: "New conversation" }).click();
  await ask(page, "I need to make an appointment");
  await page.getByRole("button", { name: "Medical appointment" }).click();
  await expect(page.getByText("I want to schedule a medical appointment")).toBeVisible();
  await expect(page.locator(".msg--assistant")).toHaveCount(2);
  const history = page.getByRole("navigation", { name: "Conversation history" });
  await expect(history.locator(".sessions__item")).toHaveCount(3);
  await showQuestion(page, "first"); // show the clarification question and the chosen option
  await shot(page, "conversation-history");
});

test("resource directory with provenance", async ({ page }) => {
  await page.goto("/#/resources");
  await expect(page.locator(".resource").first()).toBeVisible();
  await shot(page, "resources");
});

test("staff sign-in is server-gated", async ({ page }) => {
  await page.goto("/#/staff");
  await expect(page.getByRole("heading", { name: "Staff sign-in" })).toBeVisible();
  await page.setViewportSize({ width: 1440, height: 640 }); // the page is short; skip the empty space
  await shot(page, "staff-signin");
});

test("reviewer: source review queue and governance dashboard", async ({ page }) => {
  expect(PASSWORD.length).toBeGreaterThan(12);
  await signIn(page, "demo.reviewer");
  await expect(page.getByRole("table")).toBeVisible();
  await shot(page, "staff-source-review");

  // A reviewer asking for admin-only data is refused by the server and audited as denied.
  expect((await page.request.get("/api/v1/admin/users")).status()).toBe(403);

  await page.getByRole("tab", { name: "Governance" }).click();
  await expect(page.getByRole("heading", { name: /Release readiness:/ })).toBeVisible();
  await shot(page, "governance-dashboard");
  await shotOf(page, ".governance .table-wrap", "governance-risk-register");
});

test("admin: observability and audit log", async ({ page }) => {
  await signIn(page, "demo.admin");
  await page.getByRole("tab", { name: "Observability" }).click();
  await expect(page.getByRole("table")).toContainText("/api/v1/chat");
  await shot(page, "observability-dashboard");

  await page.getByRole("tab", { name: "Audit log" }).click();
  await expect(page.getByRole("table")).toContainText("denied");
  await shot(page, "audit-log");
});

test.describe("dark theme", () => {
  test.use({ colorScheme: "dark" });

  test("chat answer in the dark theme", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "How do I submit immunization records?" }).click();
    await expect(page.getByRole("region", { name: "Sources" }).first()).toBeVisible();
    await showQuestion(page);
    await shot(page, "chat-dark");
  });
});

test.describe("mobile", () => {
  test.use({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });

  test("chat and resources on a phone-sized screen", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "What are the RIH hours?" }).click();
    await expect(page.getByRole("region", { name: "Sources" }).first()).toBeVisible();
    await page.evaluate(() => {
      const chat = document.querySelector(".chat") as HTMLElement;
      window.scrollTo(0, chat.getBoundingClientRect().top + window.scrollY - 12);
    });
    await shot(page, "mobile-chat");

    await page.goto("/#/resources");
    await expect(page.locator(".resource").first()).toBeVisible();
    await shot(page, "mobile-resources");
  });
});

test("every capture is a valid, non-trivial PNG", () => {
  expect(captured.length).toBeGreaterThanOrEqual(13);
  for (const name of captured) {
    const png = readFileSync(`${OUT}/${name}.png`);
    expect(png.subarray(0, 8).toString("hex"), name).toBe("89504e470d0a1a0a");
    const width = png.readUInt32BE(16);
    const height = png.readUInt32BE(20);
    expect(width, name).toBeGreaterThanOrEqual(390);
    expect(height, name).toBeGreaterThanOrEqual(200);
  }
});
