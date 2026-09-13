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
- `scripts/acquire_sources.py`: live endpoint acquisition and provenance manifest CLI;
- `scripts/probe_sources.py`: ArcGIS source topology/CRS/extent probe;
- `scripts/select_terrain_source.py`: DEM sidecar selection and provenance-report CLI;
- `scripts/acquire_vector_sources.py`: bounded, paginated ArcGIS vector acquisition CLI;
- `scripts/validate_vector_artifacts.py`: acquisition-manifest and per-layer artifact validation CLI;
- `scripts/generate_precomputed_routes.py`: static route-asset generation CLI for a validated normalized-grid bundle;
- `scripts/acquire_copernicus_dem.py`: persistent-storage Copernicus fallback acquisition CLI;
- `scripts/cleanup_acquisition_storage.py`: dry-run-first cleanup for abandoned acquisition directories;
- `config/model.json`: S1 endpoints, seven sensitivity components, normalization, and approved sensitivity presets;
- `pyproject.toml`: minimal dependency-free Python package metadata;
- `tests/`: sixty-three standard-library unit tests covering cost, configuration, routing, source acquisition, vector acquisition, artifact validation, vector schema normalization, DEM acquisition/validation, terrain selection, and precomputed route assets;
- `benchmarks/benchmark_routing.py` and `benchmarks/results.json`: reproducible proxy benchmark;
- `docs/ANALYTICAL_MODEL.md`: model semantics, evidence, and current execution boundary.

There is still no verified evidence of:

- React/TypeScript frontend code or MapLibre integration;
- complete acquisition coverage for the full constraint-source stack;
- generated geographic cost surfaces, routes, or assessment assets;
- CI, deployment configuration, or a live application.

The feasibility record remains source evidence and scenario context. Source acquisition
is implemented for fixed endpoints and bounded ArcGIS vector layers, with staged
streaming output, tiled object-ID inventories, retries, persistent page caching,
resumption, and explicit storage limits. Live end-to-end captures for NPWS Estate,
roads, hydrography area, and rail were previously verified only in external storage;
no raw source artifacts are tracked in Git. Current count-only probes returned
216,808 SVTM and 68,320 Hydroline features in S1, but full SVTM/Hydroline
materialization is paused after a local disk-usage incident. The original temporary
files were deleted, so the project cannot attribute the incident definitively.

The approved public Copernicus GLO-30 fallback acquisition and tile validation were
implemented and successfully exercised before temporary staging was cleared. No
DEM artifact is currently present; the reproducible command writes to the persistent
external path documented in `docs/ACQUISITION_OPERATIONS.md`. No raster pixels have
been processed into an analysis grid.

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

- full external capture of the 68,320-feature hydrography-line layer and the
  approximately 216,808-feature native-vegetation layer; the road and
  hydrography-area captures are verified externally. The bounded vector adapter,
  staged streaming writer, and source-specific page-size policy are implemented
  while raw captures remain outside version control;
- actual persistent ELVIS/NSW DEM acquisition and local artifact availability;
  Copernicus GLO-30 is the implemented public fallback if the primary artifact is
  unavailable or invalid, but its temporary test capture was cleared;
- disk-safe resumption of full SVTM/Hydroline materialization after review of
  `docs/ACQUISITION_OPERATIONS.md`; large live acquisition is intentionally paused;
- normalization details;
- routing grid resolution;
- geographic source coverage and data-quality validation;
- geographic grid construction, offline route generation from those grids, and route assessment;
- inclusion or exclusion of a flood constraint;
- inclusion of DXF export.

## Deployment State

No deployment is verified.

No hosting provider is selected as a confirmed implementation decision.

## Test / Validation State

Verified on 13 September 2026:

- `PYTHONPATH=src python3 -m unittest discover -s tests -v` — 63 tests passed after the acquisition-safety and DEM changes;
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
- `PYTHONPATH=src python3 scripts/probe_sources.py --output /tmp/ico-source-probe-svtm.json --timeout 30` — live topology probe validated the configured SVTM ArcGIS feature service and layer metadata at EPSG:3308; no full SVTM artifact was published.
- bounded count-only probes returned 216,808 SVTM and 68,320 Hydroline features; 20-feature geometry samples measured approximately 8.1 KB and 0.77 KB per serialized feature respectively. No full high-volume artifact was published.
- `PYTHONPATH=src python3 scripts/acquire_copernicus_dem.py --output-dir /tmp/ico-dem-glo30-s1 --timeout 120 --max-retries 3 --backoff 1` — successfully acquired and validated four public GLO-30 tiles covering S1 in temporary external storage; that temporary artifact was subsequently cleared during incident response and is not current repository data.

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
ArcGIS vector acquisition boundary, staged streaming publication path, external road
and hydrography-area captures, artifact-integrity gate, and source-preserving vector
schema normalization are verified. The approved SVTM feature layer is configured and
topology-validated but remains unmaterialized because its S1 envelope is large and
full capture has not completed; hydrography-line capture is also unmaterialized.
Full high-volume materialization is currently paused pending owner review of the
storage audit and safe-resume workflow. The next connected work after that boundary
is DEM/raster-vector derivation and aligned grid construction, followed by route
assessment and the three geographic offline routes. The route-asset execution
boundary is implemented and tested, but no geographic route is claimed. No frontend
implementation should precede those data and model checks.
