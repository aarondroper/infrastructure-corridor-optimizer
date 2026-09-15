# MVP browser verification and preset calibration evidence

## Outcome

Completed 15 September 2026. The static S1 MVP was verified against a production-
style Vite preview in Chromium. The verification covered the default Balanced
state, all three preset switches, route centerline and endpoint visibility, map
bounds and controls, feature inspection, GeoJSON/CSV downloads, keyboard focus,
asset failure handling, console/page errors, local failed requests, and responsive
initial loads at 1440×900, 1280×800, 768×1024, and 390×844. Representative screenshots are
retained outside Git in `web/artifacts/browser-verification/`.

A real defect was corrected: the initial desktop map could retain an undersized
MapLibre canvas after the layout grew, and the MapLibre inline GeoJSON worker path
did not produce renderable route features in the production preview, including for
small probe geometries. The app now resizes the map through `ResizeObserver` and
draws the static precomputed route/endpoints in a camera-synchronized SVG overlay
over the MapLibre basemap. This keeps routing offline/precomputed and makes route
visibility deterministic. A contrasting selected-route casing and explicit focus
ring were also added.

The independent route evidence is recorded in `docs/ROUTE_ASSESSMENT.md`. The
classification is **presets behave credibly as intended; no calibration currently
justified**. No approved weights, exclusions, constraint interpretation, or preset
philosophy were changed.

## Validation

- `npm run build` — passed; only the expected MapLibre bundle-size warning remains.
- `PLAYWRIGHT_BROWSERS_PATH=/tmp/ico-browser-cache npm run test:browser` — 3 tests
  passed.
- `npm audit --omit=dev --audit-level=high` — 0 production vulnerabilities.
- Base and GIS-backed Python test suites — retained prior passing evidence: 85 tests
  passed, with three optional-GIS skips in the base interpreter.

## Remaining boundary

No deployment provider or credentials are configured in the repository, so live
deployment verification remains a separate owner/provider action. The app still
depends on public OpenStreetMap raster tiles at runtime. Automated accessibility
auditing is not included; the browser checks cover basic focus, labels, contrast,
responsive layout, and keyboard-operable controls.

## Risks / limitations

The assessment remains a preliminary 100 m grid-centerline comparison. Vegetation
is sampled from the validated raster representation, and vector crossing counts are
source-record counts rather than construction-grade physical crossing totals.
