import { randomBytes } from "node:crypto";
import { defineConfig, devices } from "@playwright/test";

// Regenerates the README screenshots from the real application: the FastAPI backend with a
// throwaway SQLite database (model features off) and the production frontend build served by
// `vite preview`, both on loopback only. All data is synthetic.
//   npm --prefix frontend run screenshots
const python = process.env.RIH_PYTHON ?? "python";
const apiPort = Number(process.env.RIH_SHOTS_API_PORT ?? 8766);
const webPort = Number(process.env.RIH_SHOTS_WEB_PORT ?? 4174);
// Synthetic staff accounts get a fresh random password per run; it is never captured.
process.env.RIH_E2E_STAFF_PASSWORD ??= `shots-${randomBytes(12).toString("hex")}`;

export default defineConfig({
  testDir: "./screenshots",
  timeout: 60_000,
  retries: 0,
  workers: 1,
  reporter: [["list"]],
  use: {
    ...devices["Desktop Chrome"],
    baseURL: `http://127.0.0.1:${webPort}`,
    viewport: { width: 1440, height: 960 },
    deviceScaleFactor: 1.5,
    colorScheme: "light",
    reducedMotion: "reduce",
    locale: "en-US",
    timezoneId: "America/New_York",
    trace: "off",
  },
  webServer: [
    {
      command: `"${python}" ../scripts/dev/e2e_backend.py --port ${apiPort}`,
      url: `http://127.0.0.1:${apiPort}/api/v1/health`,
      env: {
        RIH_E2E_STAFF_PASSWORD: process.env.RIH_E2E_STAFF_PASSWORD,
        RIH_E2E_STAFF_PREFIX: "demo",
        RIH_ALLOWED_ORIGINS: `http://127.0.0.1:${webPort}`, // the preview server is the only browser origin
      },
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: `npx vite build && npx vite preview --port ${webPort} --strictPort`,
      url: `http://127.0.0.1:${webPort}`,
      reuseExistingServer: false,
      timeout: 120_000,
      env: { RIH_BACKEND_URL: `http://127.0.0.1:${apiPort}` },
    },
  ],
});
