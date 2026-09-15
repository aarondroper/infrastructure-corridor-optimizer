import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs/promises";

const screenshotRoot = "artifacts/browser-verification";

async function attachIssueCapture(page: Page) {
  const issues: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") issues.push(`console: ${message.text()}`);
  });
  page.on("pageerror", (error) => issues.push(`pageerror: ${error.message}`));
  page.on("requestfailed", (request) => {
    const url = request.url();
    if (!url.includes("tile.openstreetmap.org")) issues.push(`request: ${url} · ${request.failure()?.errorText ?? "failed"}`);
  });
  return issues;
}

test("desktop production flow loads, switches routes, inspects impacts, and exports", async ({ page }) => {
  const issues = await attachIssueCapture(page);
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /One corridor, three defensible trade-offs/ })).toBeVisible();
  await expect(page.locator(".preset.selected")).toContainText("Balanced");
  await expect(page.locator(".map canvas")).toBeVisible();
  await expect(page.locator(".map-badge")).toContainText("Balanced");
  await expect(page.locator(".map-wrap")).toHaveAttribute("data-map-layers", "basemap,route-overlay,endpoints,endpoint-labels");
  await expect(page.locator(".route-overlay")).toHaveAttribute("data-rendered-route-features", "3");
  await expect(page.locator(".route-overlay")).toHaveAttribute("data-rendered-endpoint-features", "2");
  await expect(page.locator(".route-line-selected")).toHaveCount(1);
  await expect(page.locator(".route-endpoint text").filter({ hasText: "Bayswater" })).toBeVisible();
  await expect(page.locator(".route-endpoint text").filter({ hasText: "Eraring" })).toBeVisible();

  for (const preset of ["Shortest", "Balanced", "Environmental"]) {
    await page.locator(".preset").filter({ has: page.locator("strong", { hasText: new RegExp(`^${preset}$`) }) }).click();
    await expect(page.locator(".map-badge")).toContainText(`${preset} route selected`);
    await expect(page.locator(".preset.selected")).toContainText(preset);
    await expect(page.locator(".route-line-selected")).toHaveCount(1);
    await expect(page.locator(".route-line-selected")).toHaveAttribute("data-preset", preset.toLowerCase());
  }

  const firstDetails = page.locator(".inventory-details details").first();
  await firstDetails.locator("summary").click();
  await expect(firstDetails.locator("li").first()).toBeVisible();

  const geoDownload = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export GeoJSON" }).click();
  const geo = await geoDownload;
  expect(geo.suggestedFilename()).toBe("environmental-route.geojson");
  const geoPath = await geo.path();
  expect(await fs.readFile(geoPath!, "utf8")).toContain('"LineString"');

  const csvDownload = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export crossings CSV" }).click();
  const csv = await csvDownload;
  expect(csv.suggestedFilename()).toBe("environmental-crossings.csv");
  const csvPath = await csv.path();
  expect((await fs.readFile(csvPath!, "utf8")).split("\n")[0]).toContain("source_object_id");

  const firstButton = page.locator("button").first();
  await firstButton.focus();
  await expect(firstButton).toBeFocused();
  const focusOutline = await firstButton.evaluate((element) => getComputedStyle(element).outlineStyle);
  expect(focusOutline).toBe("solid");

  await fs.mkdir(screenshotRoot, { recursive: true });
  await page.screenshot({ path: `${screenshotRoot}/desktop-1440.png`, fullPage: true });
  expect(issues, issues.join("\n")).toEqual([]);
});

test("responsive viewports preserve the map and avoid horizontal overflow", async ({ page }) => {
  const issues = await attachIssueCapture(page);
  for (const viewport of [
    { name: "laptop-1280", width: 1280, height: 800 },
    { name: "tablet-768", width: 768, height: 1024 },
    { name: "mobile-390", width: 390, height: 844 },
  ]) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto("/");
    await expect(page.locator(".map")).toBeVisible();
    await expect(page.locator(".panel")).toBeVisible();
    await expect(page.locator(".route-overlay")).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, `${viewport.name} horizontal overflow`).toBeLessThanOrEqual(1);
    await fs.mkdir(screenshotRoot, { recursive: true });
    await page.screenshot({ path: `${screenshotRoot}/${viewport.name}.png`, fullPage: true });
  }
  expect(issues, issues.join("\n")).toEqual([]);
});

test("asset failure produces a usable error state", async ({ page }) => {
  await page.route("**/data/routes.json", (route) => route.abort());
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Corridor assets unavailable" })).toBeVisible();
  await expect(page.getByText(/Asset request failed|Failed to fetch|ERR_FAILED/)).toBeVisible();
});
