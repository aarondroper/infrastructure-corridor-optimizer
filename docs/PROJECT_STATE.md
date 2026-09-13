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
- `src/ico_model/terrain.py`: local DEM sidecar validation and explicit primary/fallback selection;
- `scripts/acquire_sources.py`: live endpoint acquisition and provenance manifest CLI;
- `scripts/probe_sources.py`: ArcGIS source topology/CRS/extent probe;
- `scripts/select_terrain_source.py`: DEM sidecar selection and provenance-report CLI;
- `scripts/acquire_vector_sources.py`: bounded, paginated ArcGIS vector acquisition CLI;
- `config/model.json`: S1 endpoints, seven sensitivity components, normalization, and approved sensitivity presets;
- `pyproject.toml`: minimal dependency-free Python package metadata;
- `tests/`: thirty-seven standard-library unit tests covering cost, configuration, routing, source acquisition, vector acquisition, and terrain selection behavior;
- `benchmarks/benchmark_routing.py` and `benchmarks/results.json`: reproducible proxy benchmark;
- `docs/ANALYTICAL_MODEL.md`: model semantics, evidence, and current execution boundary.

There is still no verified evidence of:

- React/TypeScript frontend code or MapLibre integration;
- complete acquisition coverage for the full constraint-source stack;
- generated geographic cost surfaces, routes, or assessment assets;
- CI, deployment configuration, or a live application.

The feasibility record remains source evidence and scenario context. Source acquisition
is implemented for fixed endpoints and bounded ArcGIS vector layers, with staged
streaming output and live end-to-end captures verified for NPWS Estate, roads,
hydrography area, and the railway layer into `/tmp` only.
Terrain source selection has an explicit, tested local-artifact boundary, but no DEM
has been acquired into this repository and no raster pixels have been processed.

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
dependency-light cost/routing core, approved sensitivity configuration, endpoint
acquisition boundary, unit tests, and deterministic routing benchmark are present. The
core and acquisition boundary have no GIS dependency by design; the full geographic
source-to-route pipeline remains future work.

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

Priority 2 is complete. Priority 3 is active: the transparent model schema, tested
grid operations, approved sensitivity configuration, synthetic benchmark, A* selection,
offline precomputed MVP boundary, fixed-endpoint acquisition slice, source-topology
probe, and bounded ArcGIS vector acquisition boundary are verified. Full source
materialization, raster/vector derivation, route assessment, and application assets
are not implemented.

## Open Inputs / Limitations

Feasibility research has been performed against official source catalogues/services
and representative live endpoints. The following inputs remain unresolved:

- full external capture of the hydrography-line layer, plus terrain and native-
  vegetation acquisition; the road and hydrography-area captures are verified
  externally. The bounded vector adapter, staged streaming writer, and source-specific
  page-size policy are implemented while raw captures remain outside version control;
- actual ELVIS/NSW DEM acquisition and local artifact availability; Copernicus GLO-30
  is the approved fallback if the primary artifact is unavailable or invalid;
- normalization details;
- routing grid resolution;
- geographic source coverage and data-quality validation;
- implementation of offline route generation and route assessment;
- inclusion or exclusion of a flood constraint;
- inclusion of DXF export.

## Deployment State

No deployment is verified.

No hosting provider is selected as a confirmed implementation decision.

## Test / Validation State

Verified on 13 September 2026:

- `PYTHONPATH=src python3 -m unittest discover -s tests -v` — 37 tests passed;
- `PYTHONPATH=src python3 benchmarks/benchmark_routing.py --sizes 128 256 512` — completed and retained in `benchmarks/results.json`;
- `PYTHONPATH=src python3 scripts/acquire_sources.py --output <temporary manifest> --timeout 20` — live GA endpoint acquisition succeeded; the manifest was written outside the repository;
- `PYTHONPATH=src python3 scripts/probe_sources.py --output <temporary report> --timeout 20` — live probe validated GA, NPWS, hydrography, and transport; deferred SVTM WMS and reported the NSW elevation no-raster limitation;
- `PYTHONPATH=src python3 scripts/acquire_vector_sources.py --source-id nsw-npws-estate --output-dir <temporary directory> --timeout 30` — staged and published 20 NPWS polygon features in one complete page;
- `PYTHONPATH=src python3 scripts/acquire_vector_sources.py --source-id nsw-transport --component roads --output-dir <temporary directory> --timeout 30` — staged and published 46,092 road features in 308 complete pages using the configured 150-ID page size; the artifact was 34.4 MB in `/tmp` and matched its manifest count;
- `PYTHONPATH=src python3 scripts/acquire_vector_sources.py --source-id nsw-hydrography --component hydrography_area --output-dir <temporary directory> --timeout 30` — staged and published 12,652 hydrography-area features in 64 complete pages; the 15.8 MB artifact matched its manifest count and used EPSG:7856;
- `PYTHONPATH=src python3 scripts/acquire_vector_sources.py --source-id nsw-transport --component railways --output-dir <temporary directory> --timeout 30` — acquired 415 railway features in three complete pages;
- the hydrography capture was attempted after resolving sparse child-layer metadata, but the public service stalled during a later page; interruption removed the staged output and no manifest was published;
- the benchmark produced equal A*/Dijkstra path costs and fewer explored cells for A* at all three sizes;
- JSON configuration and benchmark output parse successfully through the Python standard library.

No linting, type-check, frontend build, full geographic data-validation, or deployment
verification exists yet. Git status and diff checks are available and are run before
commits.

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

Priority 3 is active. The terrain source policy, local artifact contract, bounded
ArcGIS vector acquisition boundary, staged streaming publication path, and external
road and hydrography-area captures are verified. Hydrography-line capture remains
unmaterialized because the public service stalled during a full capture attempt. The
next connected work is to address that remaining source boundary where practical,
then implement DEM/raster-vector derivation, aligned grids, route assessment, and the
three offline routes. No frontend implementation should precede those data and model
checks.
