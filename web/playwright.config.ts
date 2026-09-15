import { defineConfig, devices } from "@playwright/test";

const previewPort = Number(process.env.ICO_PREVIEW_PORT ?? "4173");
const publicBaseUrl = process.env.ICO_BASE_URL?.replace(/\/$/, "");

export default defineConfig({
  testDir: "./tests",
  outputDir: "./artifacts/browser-test-results",
  fullyParallel: false,
  forbidOnly: true,
  reporter: [["list"], ["json", { outputFile: "./artifacts/browser-results.json" }]],
  use: {
    baseURL: publicBaseUrl ?? `http://127.0.0.1:${previewPort}`,
    browserName: "chromium",
    headless: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    ...devices["Desktop Chrome"],
  },
  webServer: publicBaseUrl ? undefined : {
    command: `npm run preview -- --host 127.0.0.1 --port ${previewPort}`,
    url: `http://127.0.0.1:${previewPort}`,
    reuseExistingServer: false,
    timeout: 30_000,
  },
});
