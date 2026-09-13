# Project State

## Purpose of This File

This is the authoritative factual snapshot of the Infrastructure Corridor Optimizer repository. It should describe current reality, not planned architecture and not chronological history.

Update this file whenever implementation, validation, deployment, data readiness, or the development frontier materially changes.

## Current Verified State

### Repository implementation

The repository contains the governance baseline, feasibility evidence, an explicit
approved sensitivity model, a dependency-light Python routing core, configuration, tests,
and a deterministic benchmark. The implemented files are:

- `src/ico_model/cost.py`: normalization, weight validation, and weighted cost-layer combination;
- `src/ico_model/routing.py`: deterministic eight-neighbor A* and Dijkstra routing;
- `config/model.json`: S1 endpoints, seven sensitivity components, normalization, and approved sensitivity presets;
- `tests/`: twelve standard-library unit tests covering cost, configuration, and routing behavior;
- `benchmarks/benchmark_routing.py` and `benchmarks/results.json`: reproducible proxy benchmark;
- `docs/ANALYTICAL_MODEL.md`: model semantics, evidence, and current execution boundary.

There is still no verified evidence of:

- React/TypeScript frontend code or MapLibre integration;
- reproducible source-acquisition scripts or selected source datasets;
- generated geographic cost surfaces, routes, or assessment assets;
- CI, deployment configuration, or a live application.

The feasibility record remains source evidence and scenario context; it is not a data
ingestion pipeline or geographic route result.

The hidden `.agents` and `.codex` directories are empty in the inspected workspace.
There is no README or package manifest yet; the source tree, executable benchmark, and
project-specific analytical configuration are now present as listed above.

The workspace has a `.git` directory entry, but it contains no usable Git metadata: `git -C . status`, `git -C . rev-parse --show-toplevel`, and `git -C . log` all fail with “not a git repository”. Commit history, tracked/untracked state, and a Git diff therefore cannot be verified here.

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

The governance files are present in the workspace. Their commit status cannot be established because the available `.git` directory is not a usable repository.

## Implemented

The governance baseline, study/data feasibility record, analytical model definition,
dependency-light cost/routing core, approved sensitivity configuration, unit tests, and
deterministic routing benchmark are present. The core has no GIS dependency by design;
the full source-to-route pipeline remains future work.

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

Priority 2 is complete: the transparent model schema, tested grid operations, approved
sensitivity configuration, synthetic benchmark, A* selection, and offline precomputed
MVP boundary are verified. Geographic source acquisition, raster/vector derivation,
route assessment, and application assets are not implemented.

## Open Inputs / Limitations

Feasibility research has been performed against official source catalogues/services
and representative live endpoints. The following inputs remain unresolved:

- final source acquisition choices and tile/feature coverage validation;
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

- `PYTHONPATH=src python3 -m unittest discover -s tests -v` — 12 tests passed;
- `PYTHONPATH=src python3 benchmarks/benchmark_routing.py --sizes 128 256 512` — completed and retained in `benchmarks/results.json`;
- the benchmark produced equal A*/Dijkstra path costs and fewer explored cells for A* at all three sizes;
- JSON configuration and benchmark output parse successfully through the Python standard library.

No linting, type-check, frontend build, geographic data-validation, or deployment
verification exists yet. Git metadata was tested and found unusable as noted above.

## Owner Decision Status

The current owner-level analytical decisions are recorded in `docs/DECISIONS.md`:
S1, the public Bayswater/Eraring endpoints, penalty treatment, the three sensitivity
presets, and offline precomputed routes for the static MVP. Future changes to the
study envelope, constraint philosophy, preset assumptions, or interactive weighting
scope must be reviewed if they materially change the product.

## Current Development Frontier

Priority 2 is complete. The next frontier is Priority 3: implement source acquisition,
coverage checks, geographic grid derivation, and offline generation of the approved
sensitivity routes. No frontend implementation should precede those data and model
checks.
