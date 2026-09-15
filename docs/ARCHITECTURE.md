# Architecture

The Infrastructure Corridor Optimizer is a reproducible offline geospatial build
that publishes a small static application. It has no application server,
database, browser-side routing engine, or server-side deployment code.

## System flow

```text
approved public sources
        ↓
validated persistent source artifacts
        ↓
100 m EPSG:7856 geographic grid and normalized costs
        ↓
deterministic A* routes and independent route assessment
        ↓
compact web/public/data/routes.json
        ↓
React + TypeScript + MapLibre static application
        ↓
Cloudflare static hosting
```

The current published scenario is S1: fixed Bayswater and Eraring endpoints in
the Hunter / New England study envelope. The analytical workflow is preliminary
corridor screening, not engineering, permitting, cadastral, or construction
approval.

## Offline analytical pipeline

Python modules under `src/ico_model/` and command-line scripts under `scripts/`
provide the following implemented stages:

- bounded ArcGIS and official-package acquisition with manifests and storage
  safeguards;
- source topology, CRS, schema, coverage, and artifact validation;
- DEM and classified SVTM raster preparation plus vector rasterization;
- seven-component normalized cost-grid derivation in EPSG:7856 at 100 m;
- deterministic eight-neighbor A* routing, with Dijkstra comparison support;
- independent physical route assessment, feature inventories, and exports;
- packaging of the selected scenario into `web/public/data/routes.json`.

The analytical configuration is versioned at `config/model.json`. Route geometry,
metrics, inventories, and export schemas are generated outputs; they are not
manually drawn or changed for presentation.

## Source and artifact boundaries

Public source metadata, licenses, versions, acquisition decisions, and current
artifacts are catalogued in [DATA_SOURCES.md](DATA_SOURCES.md). Large raw
datasets, caches, staging directories, DEM tiles, package archives, grids, and
intermediate route artifacts remain in Git-ignored `data/` storage outside the
public repository. The compact published route asset and benchmark results are
tracked because they are part of the reproducible demonstration.

The storage contract, resumability rules, safety limits, cleanup procedure, and
source-specific acquisition commands are documented in
[ACQUISITION_OPERATIONS.md](ACQUISITION_OPERATIONS.md).

## Web application

The `web/` application is a static React/TypeScript build. `App.tsx` loads the
compact route asset, switches among the three precomputed strategies, presents
the route assessment and comparison dock, and provides the existing GeoJSON and
CSV downloads. MapLibre supplies the OpenStreetMap-based contextual map and
controls. A camera-synchronized SVG overlay renders the route centerlines and
fixed endpoints without moving route computation into the browser. The
application uses self-hosted Source Sans 3 assets.

## Deployment

The deployment contract is:

| Setting | Value |
| --- | --- |
| repository branch | `main` |
| frontend root | `web` |
| build command | `npm run build` |
| build output | `dist` relative to `web` (`web/dist` in the repository) |
| environment variables | none expected |
| server-side code | none |

The live static deployment is verified at
`https://infrastructure-corridor-optimizer.aaronroper.workers.dev`. The host is
an edge-hosted static origin; the repository does not infer a Cloudflare account
or project identity from that hostname. The generated `web/_headers` file
provides cache directives for immutable hashed assets and short-lived caching for
the route data asset. See [DEPLOYMENT.md](DEPLOYMENT.md) for release checks.

## Technical boundaries

The browser is intentionally a presentation and inspection layer over validated
offline outputs. Changing endpoints, source interpretation, hard exclusions,
cost weights, preset definitions, grid resolution, or route metrics is an
analytical change and requires corresponding model evidence and documentation.
The application must continue to preserve the preliminary-screening limitations
described in [ANALYTICAL_MODEL.md](ANALYTICAL_MODEL.md).
