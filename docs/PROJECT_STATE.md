# Project State

## Purpose of This File

This is the authoritative factual snapshot of the Infrastructure Corridor Optimizer repository. It should describe current reality, not planned architecture and not chronological history.

Update this file whenever implementation, validation, deployment, data readiness, or the development frontier materially changes.

## Current Verified State

### Repository implementation

The repository contains the governance baseline, feasibility evidence, an explicit
approved sensitivity model, a dependency-light Python routing core, configuration,
tests, source-acquisition code, and a deterministic benchmark. The implemented files
are:

- `src/ico_model/cost.py`: normalization, weight validation, and weighted cost-layer combination;
- `src/ico_model/routing.py`: deterministic eight-neighbor A* and Dijkstra routing;
- `src/ico_model/sources.py`: bounded ArcGIS REST access and endpoint validation;
- `src/ico_model/vector_artifacts.py`: external vector-manifest and artifact integrity validation;
- `src/ico_model/vector_schema.py`: source-preserving canonical schemas for the seven vector components;
- `src/ico_model/precomputed_routes.py`: normalized-grid validation, approved-preset A* execution, and staged route-asset publication;
- `src/ico_model/terrain.py`: local DEM sidecar validation and explicit primary/fallback selection, including validated Copernicus tile sets;
- `src/ico_model/dem_acquisition.py`: public Copernicus GLO-30 tile selection, atomic checksum-reusing downloads, GeoTIFF/XML validation, and tile manifests;
- `src/ico_model/svtm_package.py`: guarded resumable acquisition, ZIP safety inspection, selected-member extraction, and analytical content-report validation for the official SVTM bulk delivery;
- `src/ico_model/svtm_raster.py`: direct `/vsizip` inspection of the official classified SVTM raster, VAT/metadata validation, and bounded S1 window materialization;
- `src/ico_model/geographic_grid.py`: validated-source reprojection, vector rasterization, terrain slope derivation, and seven-component S1 grid construction;
- `src/ico_model/route_impacts.py`: spatial-indexed feature-level vector inventories and SVTM raster-class inventories for route impacts;
- `src/ico_model/route_assessment.py`: route georeferencing, independent physical metrics, feature inventories, endpoint/grid-quality diagnostics, and preset comparison;
- `scripts/acquire_sources.py`: live endpoint acquisition and provenance manifest CLI;
- `scripts/probe_sources.py`: ArcGIS source topology/CRS/extent probe;
- `scripts/select_terrain_source.py`: DEM sidecar selection and provenance-report CLI;
- `scripts/acquire_vector_sources.py`: bounded, paginated ArcGIS vector acquisition CLI;
- `scripts/validate_vector_artifacts.py`: acquisition-manifest and per-layer artifact validation CLI;
- `scripts/generate_precomputed_routes.py`: static route-asset generation CLI for a validated normalized-grid bundle;
- `scripts/acquire_copernicus_dem.py`: persistent-storage Copernicus fallback acquisition CLI;
- `scripts/acquire_svtm_package.py`: persistent-storage SVTM bulk-package acquisition and validation CLI;
- `scripts/validate_svtm_raster.py`: bounded validation and provenance publication for the owner-supplied SVTM raster package;
- `scripts/derive_geographic_grid.py`: geographic S1 normalized-grid build CLI;
- `scripts/assess_routes.py`: route GeoJSON and preliminary assessment CLI;
- `scripts/build_web_assets.py`: compact static application-asset builder;
- `scripts/cleanup_acquisition_storage.py`: dry-run-first cleanup for abandoned acquisition directories;
- `config/model.json`: S1 endpoints, seven sensitivity components, normalization, and approved sensitivity presets;
- `pyproject.toml`: minimal Python package metadata with an optional `geospatial` extra for raster/vector processing;
- `tests/`: automated coverage includes cost, configuration, routing, source acquisition, vector acquisition, artifact validation, vector schema normalization, DEM acquisition/validation, terrain selection, geographic outputs, route-impact logic, compact web assets, precomputed route assets, SVTM package safeguards, and acquisition cleanup;
- `benchmarks/benchmark_routing.py` and `benchmarks/results.json`: reproducible proxy benchmark;
- `docs/ANALYTICAL_MODEL.md`: model semantics, evidence, and current execution boundary.
- `docs/ROUTE_ASSESSMENT.md`: verified S1 route metrics, preset interpretation, and
  calibration classification;
- `web/src/App.tsx`, `web/src/styles.css`, `web/src/main.tsx`, `web/tests/mvp.spec.ts`,
  and `web/playwright.config.ts`: static application shell, Source Sans 3 visual
  system, and bounded production-preview/browser verification;

There is still no verified evidence of:

- account-level Cloudflare project metadata; the live static application is verified at
  the corrected `workers.dev` origin, but the public response does not identify a
  Pages project name or source commit;
- CI or linting configuration;
- a DXF export or arbitrary client-side routing.

The feasibility record remains source evidence and scenario context. Source acquisition
is implemented for fixed endpoints and bounded ArcGIS vector layers, with staged
streaming output, tiled object-ID inventories, retries, persistent page caching,
resumption, and explicit storage limits. No raw source artifacts are tracked in Git.
Hydroline is now fully captured and independently validated in persistent external
storage. The owner-supplied official Data.NSW/SEED bulk package for the same approved
SVTM C2.0.M2.2 release is now verified: it is a valid 4,720,800,490-byte ZIP with
SHA-256 `e8d92c9a2b661b4265df90e239608a7a6e7c17bde0d57809a08f67182b187952`, 72
members, and valid CRCs. It contains the classified 5 m GeoTIFF/VAT analytical
representation, a Quickview ESRI geodatabase, and MXD symbology. The raster was
read directly from the ZIP and a complete S1 100 m output was published under
ignored persistent storage; the statewide geodatabase was not extracted because
its declared 12.6 GB size exceeds the 8 GB extraction limit. Raster use preserves
the approved native-vegetation/PCT interpretation; exact reconciliation to the
known 216,808 REST polygon count is explicitly not applicable to the raster form.

The approved public Copernicus GLO-30 fallback is now restored at
`data/external/dem/copernicus-glo30-s1/`: four EPSG:4326 one-arcsecond tiles,
complete S1 coverage, validated XML nodata `-32767`, and 160,523,100 bytes including
metadata. No raster pixels have been processed into an analysis grid.

The hidden `.agents` and `.codex` directories are empty in the inspected workspace.
There is no README yet; the source tree, executable benchmark, package manifest, and
project-specific analytical configuration are present as listed above.

The repository is a usable Git repository on branch `main`; commit history and Git
diff/status checks are available.

### Governance

The governance framework consists of:

- `AGENTS.md`;
- `docs/PROJECT_BRIEF.md`;
- `docs/ARCHITECTURE.md`;
- `docs/PROJECT_STATE.md`;
- `docs/BACKLOG.md`;
- `docs/DECISIONS.md`;
- `docs/QUALITY_GATES.md`;
- `docs/STUDY_AND_DATA_FEASIBILITY.md`;
- `docs/plans/active/`;
- `docs/plans/completed/`.

The governance files are present in the workspace and are versioned in the Git
repository.

## Implemented

The governance baseline, study/data feasibility record, analytical model definition,
dependency-light cost/routing core, approved sensitivity configuration, endpoint and
vector acquisition boundary, optional GIS preprocessing stage, unit tests, and
deterministic routing benchmark are present. Geographic grid derivation, real S1
offline routes, feature-level route assessments, compact web assets, and the first
static frontend are implemented; deployment remains future work.

## Verified

The project definition supports the following verified **project-level intentions/decisions**, not implementation claims:

- the product is an Infrastructure Corridor Optimizer for preliminary corridor screening;
- New South Wales, Australia is the default geographic direction;
- Scenario S1 is selected: an Upper Hunter to Lake Macquarie / Eraring-area context;
- the fixed endpoints are the current public Geoscience Australia Bayswater and major Eraring records captured in `config/model.json`;
- the analytical direction is weighted least-cost routing;
- the seven sensitivity model components are length, terrain, protected land, native vegetation, hydrography, roads, and railways;
- environmental and crossing factors are weighted penalties rather than universal hard exclusions;
- the three route-strategy sensitivity presets are Shortest, Balanced, and Environmental;
- offline precomputed routes are the approved static-MVP execution boundary;
- route assessment should use understandable physical metrics;
- Python is the intended processing language;
- React + TypeScript + MapLibre are the intended frontend technologies;
- reproducible automated preprocessing and static/predominantly static deployment are preferred;
- PostGIS is not required without a concrete need;
- GeoJSON and CSV exports are intended;
- DXF export is desirable but conditional.

These are preserved in `docs/DECISIONS.md` and do not establish that corresponding implementation exists.

## Partially Implemented

Priority 2 and the core Priority 3/4 analytical deliverables are complete for the
current S1 slice. The complete approved source stack, 100 m geographic grid, three
real offline routes, feature-level vector/raster impact inventories, physical route
metrics, plausibility diagnostics, and a 327,336-byte compact web asset are present in
ignored persistent storage or generated application source. The first static
React/TypeScript + MapLibre MVP is implemented, builds locally, and has passed
bounded Chromium production-preview verification at desktop, laptop, tablet, and
mobile viewports. MapLibre supplies the basemap and a synchronized SVG overlay
supplies the precomputed route centerlines/endpoints; this avoids an observed
MapLibre GeoJSON-worker loading failure while preserving the static architecture.
The current shell is compact and map-first: desktop uses strategy rail, map, and
assessment columns with an integrated comparison strip; tablet and mobile use
intentional stacked layouts.
The previously deployed public origin remains verified for commit `6c4d543`; the
current application-shell commit has not been publicly redeployed in this milestone.

## Open Inputs / Limitations

Feasibility research has been performed against official source catalogues/services
and representative live endpoints. The following inputs remain unresolved:

- exact vector-form SVTM reconciliation remains a fallback/validation question; the
  approved classified raster representation is accepted for the model and its known
  REST vector count of 216,808 is not applied as a raster feature count;
- future calibration of provisional normalization and penalty mappings remains an
  open analytical option, but the current three-route evidence review found no
  calibration justified;
- inclusion or exclusion of a flood constraint;
- inclusion of DXF export.

## Deployment State

Cloudflare Pages remains the selected repository deployment target, with root
directory `web`, build command `npm run build`, output directory `dist`, and no
environment variables. The static application is live and verified at
`https://infrastructure-corridor-optimizer.aaronroper.workers.dev/`; the supplied
hostname omitted the initial `i` and does not resolve. The live route JSON and hashed
CSS/JavaScript match the local production artifact for commit `6c4d543` byte-for-byte.
Because the public hostname is `workers.dev`, the live response alone cannot confirm
whether the account used Pages or an intentional Worker alias, nor can it expose the
Cloudflare project name or source commit metadata.

See `docs/DEPLOYMENT_CLOUDFLARE_PAGES.md` for exact setup and post-deployment checks.

## Test / Validation State

Verified through 15 September 2026:

- `PYTHONPATH=src python3 -m unittest discover -s tests -v` — 85 tests passed, with three geospatial tests skipped because optional GIS dependencies are not installed in the base interpreter;
- `PYTHONPATH=src:. /tmp/ico-gis-venv/bin/python -m unittest discover -s tests -v` — 85 tests passed with GIS-backed route-impact tests enabled;
- `PYTHONPATH=src python3 benchmarks/benchmark_routing.py --sizes 128 256 512` — completed and retained in `benchmarks/results.json`;
- `PYTHONPATH=src python3 scripts/acquire_sources.py --output <temporary manifest> --timeout 20` — live GA endpoint acquisition succeeded; the manifest was written outside the repository;
- `PYTHONPATH=src python3 scripts/probe_sources.py --output <temporary report> --timeout 20` — live probe validated GA, NPWS, SVTM, hydrography, and transport, and reported the configured terrain services as deferred/no-raster;
- `PYTHONPATH=src python3 scripts/acquire_vector_sources.py --source-id nsw-npws-estate --output-dir <temporary directory> --timeout 30` — staged and published 20 NPWS polygon features in one complete page;
- `PYTHONPATH=src python3 scripts/acquire_vector_sources.py --source-id nsw-transport --component roads --output-dir <temporary directory> --timeout 30` — staged and published 46,092 road features in 308 complete pages using the configured 150-ID page size; the artifact was 34.4 MB in `/tmp` and matched its manifest count;
- `PYTHONPATH=src python3 scripts/acquire_vector_sources.py --source-id nsw-hydrography --component hydrography_area --output-dir <temporary directory> --timeout 30` — staged and published 12,652 hydrography-area features in 64 complete pages; the 15.8 MB artifact matched its manifest count and used EPSG:7856;
- `PYTHONPATH=src python3 scripts/acquire_vector_sources.py --source-id nsw-transport --component railways --output-dir <temporary directory> --timeout 30` — acquired 415 railway features in three complete pages;
- `PYTHONPATH=src python3 scripts/validate_vector_artifacts.py --manifest <temporary road manifest> --output <temporary report>` — validated 46,092 road features, one layer, and EPSG:7856;
- `PYTHONPATH=src python3 scripts/validate_vector_artifacts.py --manifest <temporary hydrography-area manifest> --output <temporary report>` — validated 12,652 hydrography-area features, one layer, and EPSG:7856;
- `PYTHONPATH=src python3 -c '<canonical normalization check>'` — normalized all 46,092 road and 12,652 hydrography-area features from the external validated artifacts with unique stable IDs and preserved source attributes;
- the hydrography capture was attempted after resolving sparse child-layer metadata, but the public service stalled during a later page; interruption removed the staged output and no manifest was published;
- the benchmark produced equal A*/Dijkstra path costs and fewer explored cells for A* at all three sizes;
- JSON configuration and benchmark output parse successfully through the Python standard library.
- `PYTHONPATH=src:. python3 scripts/generate_precomputed_routes.py --grid-bundle <temporary bundle> --output-dir <temporary directory>` — generated shortest, balanced, and environmental route assets and a manifest from a deterministic normalized-grid fixture.
- persistent acquisition and validation produced NPWS 20 features, roads 46,092, railways 415, hydrography-area 12,652, and hydrography-line 68,320; all five vector manifests validate in EPSG:7856 and are complete by their tiled inventories;
- ArcGIS NPWS empty tiles returned `objectIds: null`; this valid empty-result behavior is now handled and regression-tested rather than treated as a malformed response;
- `PYTHONPATH=src:. /tmp/ico-gis-venv/bin/python scripts/derive_geographic_grid.py ...` — published a real S1 100 m EPSG:7856 bundle of 990x767 cells, 8,329 unavailable DEM/SVTM nodata cells, transformed endpoint cells `[149, 125]` and `[880, 672]`, and all seven components. Shapely repaired 15 invalid NPWS polygon geometries; the other four vector inputs required no repair.
- `PYTHONPATH=src:. /tmp/ico-gis-venv/bin/python scripts/generate_precomputed_routes.py ...` — generated shortest (732 cells, 832.807 cost), balanced (741 cells, 494.735 cost), and environmental (786 cells, 311.769 cost) routes with A*;
- `PYTHONPATH=src:. /tmp/ico-gis-venv/bin/python scripts/assess_routes.py ...` with all five vector artifacts and the SVTM raster/archive — published feature-level inventories, EPSG:7844 GeoJSON, physical slope metrics, route-quality diagnostics, and independent lengths of 95.76 km, 96.28 km, and 99.17 km respectively. All routes used available cells, matched endpoint cells, avoided grid boundaries, and had simple centerlines;
- `PYTHONPATH=src python3 scripts/build_web_assets.py ...` — published a 327,336-byte static asset containing the three route geometries, metrics, compact impact inventories, endpoint features, comparison data, and screening disclaimer with raw source paths removed;
- `npm install` in `web/` — installed the declared React/TypeScript/MapLibre and Playwright browser-test dependencies;
- `npm run build` in `web/` — TypeScript and Vite production build succeeded with
  self-hosted Latin Source Sans 3 font assets; the MapLibre bundle-size warning
  remains expected for the initial MVP;
- `ICO_PREVIEW_PORT=4179 PLAYWRIGHT_BROWSERS_PATH=/tmp/ico-browser-cache npm run test:browser`
  in `web/` — all three production-preview tests passed after the visual refinement,
  covering route switching, impact inspection, exports, focus styling, the Source
  Sans 3 assertion, error handling, responsive overflow, and OSM tile responses at
  1440×900, 1280×800, 768×1024, and 390×844. Screenshots were regenerated after a
  bounded basemap-render wait and visually inspected at all four viewports;
- `ICO_PREVIEW_PORT=4181 PLAYWRIGHT_BROWSERS_PATH=/tmp/ico-browser-cache npm run test:browser`
  in `web/` — all three production-preview tests passed after the application-shell
  refactor, including shell-region assertions, slogan removal, comparison-row route
  switching, impact inspection, exports, focus, error handling, responsive overflow,
  and OSM tile responses at all four required viewports. The regenerated shell
  screenshots were visually inspected;
- `ICO_BASE_URL=https://infrastructure-corridor-optimizer.aaronroper.workers.dev ICO_STRICT_NETWORK=1 PLAYWRIGHT_BROWSERS_PATH=/tmp/ico-browser-cache npm run test:browser` in `web/` — all three public-origin tests passed at 1440×900, 1280×800, 768×1024, and 390×844, covering root reload, static assets, route switching, inspection, exports, responsive layout, error handling, focus, and OSM tile responses. Expected obsolete-tile `net::ERR_ABORTED` cancellations were excluded; no genuine network, console, or page errors were observed. Screenshots are retained under ignored `web/artifacts/browser-verification/`;
- live artifact comparison — public `routes.json`, hashed JavaScript, and hashed CSS SHA-256 values match the local production build for commit `6c4d543`; hashed assets return `public, max-age=31536000, immutable`, while `routes.json` returns `public, max-age=0, must-revalidate`;
- production artifact inspection — `web/dist/` contains `index.html`, hashed CSS/JS, `_headers`, and the 327,336-byte compact `data/routes.json`; the shell and analytical asset contain no local filesystem, development-host, raw-data, or cache references. `_headers` assigns immutable caching only to hashed `/assets/*` files;
- the browser review confirmed visible route centerlines/endpoints, map controls and bounds, route switching, feature inspection, keyboard focus, no horizontal overflow, and no captured application console/page/runtime errors or local-asset request failures. OpenStreetMap tile requests remain an external runtime dependency;
- bounded count-only probes returned 216,808 SVTM and 68,320 Hydroline features; 20-feature geometry samples measured approximately 8.1 KB and 0.77 KB per serialized feature respectively. No full SVTM vector artifact was published; the official classified raster representation is validated and accepted.
- Hydroline validation independently confirmed 68,320 unique features, 355 pages, 16 tiles, and 965 tiled-inventory overlaps reconciled. The persistent final bundle is 105,232,759 bytes and its cache namespace is 108,584,694 bytes.
- Full SVTM REST acquisition first exceeded the unchanged 32 MB response ceiling at 1,000 features/page. The page size was reduced to 250 based on observed response size; the run reached 190 validated pages, 1,159,268,449 bytes of page cache, and a 333,452,505-byte peak staged artifact before repeated ArcGIS failures. The page-250 cache remains fallback/validation evidence, not the primary source.
- The owner-supplied SVTM ZIP passed full `ZipFile.testzip()` validation. Its 5 m raster is EPSG:3308, uint16, one-band, LZW, and nodata 65535; its VAT has 1,687 records and required PCT/vegetation fields. Direct window reading produced a 789x1005 100 m S1 raster with complete envelope coverage, VAT-valid values, and approximately 0.125% nodata in the output. The package archive is 4.72 GB and exceeds the configured 4 GB archive cap; declared package extraction is 16.10 GB and exceeds the 8 GB cap, so no statewide extraction was attempted. The observed persistent package-plus-output working set was 4,721,081,685 bytes.
- The largest observed combined Hydroline/SVTM working set was approximately 1.60 GB, below the unchanged 12 GB limit; persistent `df -h .` checks retained at least 912 GB free during capture.
- `df -h .` — persistent project storage reported 911 GB available before DEM restoration.
- `PYTHONPATH=src python3 scripts/acquire_copernicus_dem.py --output-dir data/external/dem/copernicus-glo30-s1 --timeout 120 --max-retries 3 --backoff 1` — restored four public GLO-30 tiles covering S1; the persistent artifact is 160,523,100 bytes and passed the terrain artifact validator.
- `PYTHONPATH=src python3 scripts/acquire_svtm_package.py --cache-dir data/cache/seed/svtm-c2.0.m2.2 --output-dir data/external/vectors/svtm-package --timeout 15 --max-retries 0` — bounded package probe wrote only a 423-byte persistent state record and failed safely on the official endpoint's HTTP 202 web challenge; no archive bytes were materialized.

No dedicated linting/type-check command beyond the successful TypeScript compiler,
no automated accessibility audit exists yet. Public deployment verification is complete
for the live Cloudflare origin, while Pages-vs-Worker account identity remains an owner
check. Git status
and diff checks are available and are run before commits.

## Owner Decision Status

The current owner-level analytical decisions are recorded in `docs/DECISIONS.md`:
S1, the public Bayswater/Eraring endpoints, penalty treatment, the three sensitivity
presets, and offline precomputed routes for the static MVP. Future changes to the
study envelope, constraint philosophy, preset assumptions, or interactive weighting
scope must be reviewed if they materially change the product.

The terrain-source decision is resolved: use ELVIS/NSW DEM first and Copernicus DEM
GLO-30 as the explicit fallback. Actual product selection, acquisition credentials
or ordering, and any change to the approved source order remain subject to evidence
and the decision log; the selector does not silently substitute an unconfigured source.

## Current Development Frontier

The first analytical and static-MVP execution slice is complete: the approved S1
source stack, geographic grid, A* routes, feature-level assessments, compact assets,
local frontend build, and bounded browser verification are verified. The current
preset evidence is classified as credible with no calibration currently justified;
the comparison is recorded in `docs/ROUTE_ASSESSMENT.md`. The visual-system and
application-shell refinements are complete in the current tree and locally verified;
the existing public origin still serves the prior verified build until this commit is
deployed. The next frontier is the normal release of this shell commit and,
separately, any owner-reviewed analytical calibration or future product scope. No
engineering or regulatory approval is implied.
