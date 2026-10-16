// WCAG 2.x contrast checks for the design tokens in styles.css (light and dark themes).
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const css = readFileSync(resolve(__dirname, "styles.css"), "utf-8");

function block(selector: string): string {
  const start = css.indexOf(`${selector} {`);
  if (start < 0) throw new Error(`missing ${selector}`);
  return css.slice(start, css.indexOf("}", start));
}

function tokens(text: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const m of text.matchAll(/--([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})\s*;/g)) out[m[1]] = m[2].toLowerCase();
  // Aliases such as `--red: var(--umbc-red)` resolve against the palette in :root.
  for (const m of text.matchAll(/--([a-z0-9-]+):\s*var\(--([a-z0-9-]+)\)\s*;/g)) out[m[1]] = `var:${m[2]}`;
  return out;
}

function resolveAliases(t: Record<string, string>, base: Record<string, string>): Record<string, string> {
  const out = { ...t };
  for (const [k, v] of Object.entries(out)) if (v.startsWith("var:")) out[k] = base[v.slice(4)] ?? out[v.slice(4)];
  return out;
}

function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

const raw = tokens(block(":root"));
const palette = resolveAliases(raw, raw);
const light = palette;
const dark = resolveAliases({ ...palette, ...tokens(block(':root[data-theme="dark"]')) }, palette);

// [foreground, background, minimum]: 4.5 for text, 3 for focus rings, borders and icons.
const TEXT_PAIRS: [string, string][] = [
  ["text", "bg"], ["text", "surface"], ["text", "surface-2"], ["text-soft", "surface-sunken"],
  ["muted", "bg"], ["muted", "surface"], ["muted", "surface-2"], ["muted", "surface-sunken"],
  ["link", "surface"], ["link", "surface-2"], ["on-user-bubble", "user-bubble"], ["text", "gold-tint"],
  ["teal-text", "teal-tint"], ["red-text", "red-tint"], ["brown-text", "brown-tint"], ["text", "red-tint"],
];
const UI_PAIRS: [string, string][] = [["focus-ring", "surface"], ["focus-ring", "bg"], ["red", "surface"], ["teal", "surface"]];

describe.each([
  ["light", light],
  ["dark", dark],
])("%s theme contrast", (_name, t) => {
  it.each(TEXT_PAIRS)("%s on %s meets AA for text", (fg, bg) => {
    expect(contrast(t[fg], t[bg])).toBeGreaterThanOrEqual(4.5);
  });
  it.each(UI_PAIRS)("%s on %s meets 3:1 for UI components", (fg, bg) => {
    expect(contrast(t[fg], t[bg])).toBeGreaterThanOrEqual(3);
  });
});

describe("brand pairings", () => {
  it("uses black, never white, on gold", () => {
    expect(contrast("#000000", palette["umbc-gold"])).toBeGreaterThanOrEqual(4.5);
    expect(contrast("#ffffff", palette["umbc-gold"])).toBeLessThan(4.5); // why white on gold is banned
  });

  it("header text is readable on the black bar", () => {
    expect(contrast(light["header-text"], light["header-bg"])).toBeGreaterThanOrEqual(4.5);
    expect(contrast(light["header-muted"], light["header-bg"])).toBeGreaterThanOrEqual(4.5);
    expect(contrast(palette["umbc-gold"], "#000000")).toBeGreaterThanOrEqual(4.5);
  });

  it("keeps the system dark theme and the explicit dark theme identical", () => {
    expect(tokens(block(':root:not([data-theme="light"])'))).toEqual(tokens(block(':root[data-theme="dark"]')));
  });
});
