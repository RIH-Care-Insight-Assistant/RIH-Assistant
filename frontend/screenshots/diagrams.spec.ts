import { mkdirSync, readFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import { expect, test } from "@playwright/test";

// Renders the architecture diagrams from their editable HTML sources in docs/architecture/diagrams/
// to PNG files in docs/assets/architecture/. Local files only; no network.

const SRC = fileURLToPath(new URL("../../docs/architecture/diagrams/", import.meta.url));
const OUT = fileURLToPath(new URL("../../docs/assets/architecture/", import.meta.url));
mkdirSync(OUT, { recursive: true });

const DIAGRAMS: [source: string, output: string][] = [
  ["architecture.html", "system-architecture.png"],
  ["request-flow.html", "request-flow.png"],
];

test.use({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1.5, colorScheme: "light" });

for (const [source, output] of DIAGRAMS) {
  test(`render ${source}`, async ({ page }) => {
    await page.goto(pathToFileURL(SRC + source).href);
    await page.evaluate(() => document.fonts.ready);
    await page.locator("#diagram").screenshot({ path: OUT + output, animations: "disabled" });
    const png = readFileSync(OUT + output);
    expect(png.subarray(0, 8).toString("hex")).toBe("89504e470d0a1a0a");
    expect(png.readUInt32BE(16)).toBe(2400); // 1600 CSS px at 1.5x
  });
}
