# Infrastructure Corridor Optimizer

The Infrastructure Corridor Optimizer is a geospatial decision-support application
for comparing preliminary infrastructure corridors between fixed endpoints. It uses
real public NSW/Australian spatial data, weighted least-cost routing, and independent
route-impact assessment to show how different planning priorities change a corridor.

**Live application:** [infrastructure-corridor-optimizer.aaronroper.workers.dev](https://infrastructure-corridor-optimizer.aaronroper.workers.dev)

## What it demonstrates

- reproducible public-data acquisition and provenance;
- raster/vector integration and CRS-normalized GIS processing;
- terrain, environmental, and infrastructure-crossing constraints;
- transparent weighted cost surfaces and deterministic A* routing;
- route-impact and crossing assessment with GeoJSON and CSV exports;
- a static React/TypeScript + MapLibre application and edge deployment.

## Route strategies

The current S1 study compares three precomputed routes between the Bayswater area
and Eraring area in NSW:

| Strategy | Role | Length |
| --- | --- | ---: |
| Shortest | Strong preference for route length | 95.76 km |
| Balanced | Moderates length against terrain, environmental sensitivity, and crossings | 96.28 km |
| Environmental | Prioritizes lower environmental sensitivity while retaining length control | 99.17 km |

These are screening alternatives, not engineering recommendations or approved
development corridors.

## How the analysis works

```text
public source data
  → source validation, CRS normalization, and clipping
  → 100 m EPSG:7856 cost grid
  → weighted strategy costs
  → deterministic eight-neighbor A* routes
  → independent route-impact assessment
  → compact static web assets
```

See [the analytical model](docs/ANALYTICAL_MODEL.md) for the cost components,
normalization, routing, and interpretation limits.

## Data

The S1 model uses Geoscience Australia electricity-infrastructure records for the
fixed endpoints, NSW protected-area, vegetation, hydrography, road, and railway
data, and Copernicus DEM GLO-30 terrain tiles. The approved NSW State Vegetation
Type Map Extant release is C2.0.M2.2. Details, links, versions, formats, and
provenance are recorded in [Data sources](docs/DATA_SOURCES.md).

## Architecture

Python preprocessing acquires and validates source data, builds the geographic cost
grid, generates the three offline routes, and publishes compact application assets.
The `web/` project is a static React + TypeScript frontend using MapLibre for the
contextual map and a synchronized SVG overlay for route centerlines and endpoints.
The static application is deployed through Cloudflare edge hosting. See
[Architecture](docs/ARCHITECTURE.md) and [Deployment](docs/DEPLOYMENT.md).

## Running locally

Python 3.10 or newer is required. The base package has no runtime dependencies;
optional geospatial processing uses the `geospatial` extra.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[geospatial]'
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Large source acquisition and analytical regeneration are documented in
[Acquisition operations](docs/ACQUISITION_OPERATIONS.md). Raw and derived GIS
artifacts are intentionally not included in the repository.

To build and preview the frontend:

```bash
cd web
npm install
npm run build
npm run preview
```

The production frontend consumes the checked-in compact asset at
`web/public/data/routes.json`.

## Tests

The Python suite covers cost construction, routing, source and artifact validation,
DEM/SVTM handling, geographic outputs, route impacts, and web-asset generation.
The browser suite covers production-preview loading, route switching, inspection,
exports, responsive layouts, focus behavior, static assets, error handling, and
OpenStreetMap tile responses:

```bash
cd web
npm run test:browser
```

## Reproducibility

Acquisition, validation, grid derivation, route generation, assessment, and web-asset
build entry points are provided under `scripts/`. Source URLs, release information,
configuration, manifests, and safety limits are documented in the repository. Large
raw data, package archives, caches, and generated GIS intermediates belong in the
ignored `data/` locations or another controlled build environment, not in Git.

## Limitations

This is a preliminary corridor-screening product. Routes are derived from a 100 m
analysis grid and public source layers; they are not construction-ready designs and
do not replace detailed engineering, environmental assessment, land-access review,
permitting or regulatory review, or field investigation. The preset weights and
source transformations are planning assumptions, and the route assessment reports
physical indicators rather than a legal or environmental approval.

## Further documentation

- [Analytical model](docs/ANALYTICAL_MODEL.md)
- [Data sources](docs/DATA_SOURCES.md)
- [Acquisition operations](docs/ACQUISITION_OPERATIONS.md)
- [Route assessment](docs/ROUTE_ASSESSMENT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Deployment](docs/DEPLOYMENT.md)
