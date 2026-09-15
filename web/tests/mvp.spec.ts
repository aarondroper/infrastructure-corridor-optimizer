import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs/promises";

const screenshotRoot = "artifacts/browser-verification";
const strictNetwork = process.env.ICO_STRICT_NETWORK === "1";

async function attachIssueCapture(page: Page) {
  const issues: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") issues.push(`console: ${message.text()}`);
  });
  page.on("pageerror", (error) => issues.push(`pageerror: ${error.message}`));
  page.on("requestfailed", (request) => {
    const url = request.url();
    const failure = request.failure()?.errorText ?? "failed";
    const expectedTileCancellation = url.includes("tile.openstreetmap.org") && failure === "net::ERR_ABORTED";
    if (!expectedTileCancellation && (strictNetwork || !url.includes("tile.openstreetmap.org"))) {
      issues.push(`request: ${url} · ${failure}`);
    }
  });
  return issues;
}

test("desktop production flow loads, switches routes, inspects impacts, and exports", async ({ page }) => {
  const issues = await attachIssueCapture(page);
  const basemapStatuses: number[] = [];
  page.on("response", (response) => {
    if (response.url().includes("tile.openstreetmap.org")) basemapStatuses.push(response.status());
  });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Infrastructure Corridor Optimizer", exact: true })).toBeVisible();
  await expect(page.getByText(/Hunter \/ New England, NSW · Scenario S1/)).toBeVisible();
  const logo = page.locator(".app-logo");
  await expect(logo).toBeVisible();
  await expect(logo).toHaveAttribute("src", "/branding/app-logo.svg");
  const logoSize = await logo.evaluate((element: HTMLImageElement) => ({ width: element.getBoundingClientRect().width, height: element.getBoundingClientRect().height, naturalWidth: element.naturalWidth }));
  expect(logoSize.width).toBeGreaterThanOrEqual(28);
  expect(logoSize.width).toBeLessThanOrEqual(40);
  expect(logoSize.height).toBe(logoSize.width);
  expect(await logo.evaluate((element: HTMLImageElement) => element.naturalWidth)).toBeGreaterThan(0);
  expect((await page.request.get("/branding/app-logo.svg")).status()).toBe(200);
  const about = page.getByRole("button", { name: "About the analysis" });
  await expect(about).toBeVisible();
  await about.click();
  const analysisDialog = page.getByRole("dialog", { name: "About the analysis" });
  await expect(analysisDialog).toBeVisible();
  await expect(analysisDialog).toContainText("100 m");
  await expect(analysisDialog).toContainText("OpenStreetMap");
  await page.keyboard.press("Escape");
  await expect(analysisDialog).toBeHidden();
  await expect(about).toBeFocused();
  await expect(page.locator("footer")).toHaveCount(0);
  await expect(page.getByText("Preliminary corridor screening only.", { exact: false })).toHaveCount(0);
  await expect(page.getByText("One corridor, three defensible trade-offs.", { exact: true })).toHaveCount(0);
  const rootResponse = await page.request.get("/");
  expect(rootResponse.status()).toBe(200);
  const rootHtml = await rootResponse.text();
  expect(rootHtml).toContain("/assets/");
  expect(rootHtml).not.toMatch(/(?:file:\/\/|\/home\/|\/tmp\/|127\.0\.0\.1|localhost)/);
  const localAssetPaths = [...rootHtml.matchAll(/(?:src|href)="(\/assets\/[^"]+)"/g)].map((match) => match[1]);
  expect(localAssetPaths.length).toBeGreaterThan(0);
  for (const assetPath of localAssetPaths) {
    expect((await page.request.get(assetPath)).status(), assetPath).toBe(200);
  }
  const routeAssetResponse = await page.request.get("/data/routes.json");
  expect(routeAssetResponse.status()).toBe(200);
  expect(routeAssetResponse.headers()["content-type"]).toContain("application/json");
  const routeAsset = await routeAssetResponse.json();
  expect(routeAsset.routes).toHaveLength(3);
  expect(routeAsset.endpoints.features).toHaveLength(2);
  await page.reload();
  await expect(page.locator(".preset.selected")).toContainText("Balanced");
  await expect(page.locator(".map canvas")).toBeVisible();
  await expect(page.locator(".map-badge")).toContainText("Balanced");
  await expect(page.locator(".app-shell > .strategy-rail")).toBeVisible();
  await expect(page.locator(".app-shell > .map-column")).toBeVisible();
  await expect(page.locator(".app-shell > .assessment-panel")).toBeVisible();
  await expect(page.locator(".comparison-strip")).toBeVisible();
  await expect(page.locator(".map-wrap")).toHaveAttribute("data-map-layers", "basemap,route-overlay,endpoints,endpoint-labels");
  await expect(page.locator(".route-overlay")).toHaveAttribute("data-rendered-route-features", "3");
  await expect(page.locator(".route-overlay")).toHaveAttribute("data-rendered-endpoint-features", "2");
  await expect(page.locator(".map-legend-item")).toHaveCount(3);
  for (const preset of ["shortest", "balanced", "environmental"]) {
    await expect(page.locator(`.route-line[data-preset="${preset}"]:not(.route-line-casing)`)).toHaveCount(1);
  }
  await expect(page.locator(".route-line-selected")).toHaveCount(1);
  await expect(page.locator(".route-endpoint text").filter({ hasText: "Bayswater" })).toBeVisible();
  await expect(page.locator(".route-endpoint text").filter({ hasText: "Eraring" })).toBeVisible();

  for (const preset of ["Shortest", "Balanced", "Environmental"]) {
    await page.locator(".preset").filter({ has: page.locator("strong", { hasText: new RegExp(`^${preset}$`) }) }).click();
    await expect(page.locator(".map-badge")).toContainText(`${preset} route selected`);
    await expect(page.locator(".preset.selected")).toContainText(preset);
    await expect(page.locator(".route-line-selected")).toHaveCount(1);
    await expect(page.locator(".route-line-selected")).toHaveAttribute("data-preset", preset.toLowerCase());
    await expect(page.locator(".map-legend-item.selected")).toContainText(preset);
  }

  await page.locator(".table-row").filter({ hasText: "Shortest" }).click();
  await expect(page.locator(".assessment-panel h2")).toHaveText("Shortest route");
  await page.locator(".preset").filter({ has: page.locator("strong", { hasText: /^Environmental$/ }) }).click();

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

  const interfaceFont = await page.locator("h1").evaluate((element) => getComputedStyle(element).fontFamily);
  expect(interfaceFont).toContain("Source Sans 3");

  await fs.mkdir(screenshotRoot, { recursive: true });
  await page.waitForTimeout(1_000);
  await page.screenshot({ path: `${screenshotRoot}/desktop-1440.png`, fullPage: true });
  expect(basemapStatuses.some((status) => status >= 200 && status < 300), `OpenStreetMap statuses: ${basemapStatuses.join(", ")}`).toBeTruthy();
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
    await page.waitForTimeout(1_000);
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
