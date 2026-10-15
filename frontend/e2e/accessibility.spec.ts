import { expect, test } from "@playwright/test";

// Keyboard use, visible focus, theme switching and phone-width layout against the real app.

test("keyboard: skip link, visible focus ring and sending a question without a mouse", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("Tab");
  const skip = page.getByRole("link", { name: "Skip to content" });
  await expect(skip).toBeFocused();
  await expect(skip).toBeInViewport();

  await page.keyboard.press("Tab"); // first main navigation link
  const chat = page.getByRole("link", { name: "Chat" });
  await expect(chat).toBeFocused();
  const outline = await chat.evaluate((el) => getComputedStyle(el).outlineStyle);
  expect(outline).toBe("solid");

  const suggestion = page.getByRole("button", { name: "What are the RIH hours?" });
  await suggestion.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("region", { name: "Sources" }).first()).toBeVisible();

  const input = page.getByLabel("Your message");
  await input.focus();
  await page.keyboard.type("How do I submit immunization records?");
  await page.keyboard.press("Enter");
  await expect(page.locator(".msg--assistant")).toHaveCount(2);
});

test("theme toggle switches and remembers the theme", async ({ page }) => {
  await page.goto("/");
  const html = page.locator("html");
  const toggle = page.getByRole("button", { name: /^Use (dark|light) theme$/ });
  const before = (await toggle.getAttribute("aria-label")) ?? "";
  const target = before.includes("dark") ? "dark" : "light";
  await toggle.focus();
  await page.keyboard.press("Enter");
  await expect(html).toHaveAttribute("data-theme", target);
  await page.reload();
  await expect(html).toHaveAttribute("data-theme", target);
});

test("phone width has no horizontal scrolling", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 760 });
  for (const hash of ["#/chat", "#/resources", "#/staff"]) {
    await page.goto(`/${hash}`);
    await page.waitForLoadState("networkidle");
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, hash).toBeLessThanOrEqual(0);
  }
});
