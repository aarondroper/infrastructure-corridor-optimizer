# Route assessment and static MVP

## Objective

Complete the evidence-based diagnostic layer for the existing S1 shortest,
balanced, and environmental routes, then publish a compact static React/TypeScript
and MapLibre MVP around the validated precomputed assets.

## Outcome

Completed on 14 September 2026. Added spatial-indexed inventories of intersected
protected-area, hydroline, hydroarea, road, and railway source features, plus SVTM
classified-raster route-cell inventories with PCT/VAT metadata. Added route physical
slope metrics, weighted cell-exposure diagnostics, endpoint snap checks, unavailable
cell checks, boundary/simple-centerline checks, and a descriptive comparison summary.
Added the compact asset builder and a static MapLibre route comparison application
with GeoJSON and feature-level CSV exports. The approved weights, exclusions, source
interpretations, and preset philosophy were not changed.

## Validation performed

- `PYTHONPATH=src python3 -m unittest discover -s tests -v` — 85 passed, 3 GIS skips;
- `PYTHONPATH=src:. /tmp/ico-gis-venv/bin/python -m unittest discover -s tests -v` — 85 passed;
- real S1 grid re-derivation retained raw slope diagnostics;
- real route assessment completed for all three presets using all five vector
  artifacts, the validated SVTM raster, and the official package VAT;
- all three routes used available cells, matched endpoint cells, avoided grid
  boundaries, and had simple centerlines;
- `npm install`, `npm audit --omit=dev --audit-level=high`, and `npm run build` in
  `web/` — build succeeded and the final production dependency audit reported zero
  vulnerabilities;
- compact `web/public/data/routes.json` validated at 327,723 bytes without raw source
  paths or source geometries;
- `git diff --check` and manual diff/documentation review completed.

## Measured real-output summary

Shortest / Balanced / Environmental route lengths are 95.76 / 96.28 / 99.17 km.
Native-vegetation route cells are 136 / 113 / 82; hydroline intersected features
are 120 / 117 / 104; major-road intersections are 16 / 17 / 20; railway features
are 4 / 4 / 4. Mean slope is 2.76 / 2.67 / 2.69 degrees. These are descriptive
screening metrics, not a recommendation or engineering conclusion.

## Remaining limitations

The 100 m route centerline is not a surveyed corridor footprint. Source segmentation
can produce multiple feature records for one named physical crossing. The browser
application has not been deployed or browser-visual-tested, and the external
OpenStreetMap basemap remains a runtime display dependency. Model calibration,
flood-layer scope, and DXF export remain future/owner-reviewed work.
