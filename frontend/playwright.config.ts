import { defineConfig, devices } from "@playwright/test";

// End-to-end tests run the real FastAPI backend (throwaway SQLite, model features off)
// and the Vite frontend, both on loopback only.
const python = process.env.RIH_PYTHON ?? "python";
const apiPort = Number(process.env.RIH_E2E_API_PORT ?? 8765);

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: 0,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:5173",
    trace: "off",
    screenshot: "off",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `"${python}" ../scripts/dev/e2e_backend.py --port ${apiPort}`,
      url: `http://127.0.0.1:${apiPort}/api/v1/health`,
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: "npx vite --port 5173 --strictPort",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: false,
      timeout: 60_000,
      env: { RIH_BACKEND_URL: `http://127.0.0.1:${apiPort}` },
    },
  ],
});
