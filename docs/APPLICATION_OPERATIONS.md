# Static application operations

The first S1 application is a static React/TypeScript + MapLibre build. It does not
run routing in the browser. The Python pipeline validates sources, derives the grid,
generates routes, assesses impacts, and then publishes the compact data consumed by
the app.

## Build the compact asset

From the repository root, after the ignored persistent geographic outputs exist:

```bash
PYTHONPATH=src python3 scripts/build_web_assets.py \
  --assessments data/external/routes/s1-100m/route_assessments.json \
  --routes-dir data/external/routes/s1-100m \
  --config config/model.json \
  --output web/public/data/routes.json
```

The asset retains route geometry, approved preset descriptions, physical metrics,
feature-level IDs/properties, SVTM class counts, endpoint features, and the
screening disclaimer. It intentionally omits source geometry and raw cache paths.

## Install and build the app

```bash
cd web
npm install
npm run build
```

The Vite output is `web/dist/` and is ignored by Git. `web/node_modules/` is also
ignored. The app currently uses OpenStreetMap raster tiles at runtime, so a deployed
build still has a public basemap dependency; route and assessment assets are static.

To provide the final application mark, replace `web/public/branding/app-logo.svg` and
rebuild/deploy the frontend.

## Cloudflare Pages release configuration

Cloudflare Pages is the selected deployment target. Connect the GitHub repository and
set the project root to `web`, the build command to `npm run build`, and the output
directory to `dist` relative to that root. No environment variables or server-side
Cloudflare features are required. The checked-in `web/public/_headers` file applies a
long immutable cache lifetime only to Vite's hashed `/assets/*` files. The deployment
is public and verified at the documented `workers.dev` origin. The current
visual-polish and density-refinement changes are production-preview verified locally
and will take effect
publicly when the normal Cloudflare release workflow publishes this commit. The
public-origin checklist remains in
`docs/DEPLOYMENT_CLOUDFLARE_PAGES.md`.

## Browser verification

Run the production-style preview checks from `web/` after building:

```bash
ICO_PREVIEW_PORT=4174 PLAYWRIGHT_BROWSERS_PATH=/tmp/ico-browser-cache npm run test:browser
```

The suite uses Chromium against `vite preview` and verifies the desktop interaction
flow, route switching, impact inspection, exports, asset-failure handling, and
initial loads at 1440×900, 1280×800, 768×1024, and 390×844. Visual evidence is written to the
ignored `web/artifacts/browser-verification/` directory. The browser cache is an
explicit bounded verification dependency under `/tmp`, not project source storage.
The suite also checks direct root reload, application/data asset responses, and
successful OpenStreetMap tile responses when the public tile service is reachable.

The UI provides approved preset switching, key route metrics, compact impact counts,
GeoJSON download, and a feature-level crossings CSV download. It remains a
preliminary corridor-screening presentation, not engineering approval. The current
shell presents strategy, map, and assessment regions side by side on desktop, then
uses map-first stacked tablet and strategy-first mobile layouts. All three existing
route centerlines are visible in the map overlay with a compact identity legend; the
selected route is emphasized while the same identity is repeated in the strategy rail,
assessment heading, and comparison dock.

## Current limitations

- The route line follows 100 m cell centres; it is not a surveyed or constructible
  alignment.
- Feature inventories count intersected source records. Hydroline, road, and rail
  source segmentation can yield multiple records for one named physical crossing.
- The app has passed the bounded browser and visual review above. It has no automated
  accessibility audit yet, and the current map-comparison polish commit has not yet been
  reverified on the public origin. The route centerlines and endpoints are rendered as a
  camera-synchronized SVG overlay over the MapLibre basemap; the analytical route
  and assessment data remain static and precomputed.
- The basemap is external and is not an analytical input.
