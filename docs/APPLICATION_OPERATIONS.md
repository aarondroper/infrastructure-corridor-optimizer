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

The UI provides approved preset switching, key route metrics, compact impact counts,
GeoJSON download, and a feature-level crossings CSV download. It remains a
preliminary corridor-screening presentation, not engineering approval.

## Current limitations

- The route line follows 100 m cell centres; it is not a surveyed or constructible
  alignment.
- Feature inventories count intersected source records. Hydroline, road, and rail
  source segmentation can yield multiple records for one named physical crossing.
- The app has not yet undergone browser automation, deployment verification, or
  full visual/accessibility review.
- The basemap is external and is not an analytical input.
