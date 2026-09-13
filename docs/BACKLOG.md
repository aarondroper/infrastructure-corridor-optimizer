# Backlog

## Backlog Principles

This file contains prioritized **remaining work**, organized into milestones. It is not a chronological history and should not duplicate detailed execution plans.

When a milestone becomes active and requires substantial implementation, create a concise plan in `docs/plans/active/`.

## Priority 1 — Study and Data Feasibility

**Status:** Complete. Evidence is recorded in `docs/STUDY_AND_DATA_FEASIBILITY.md`;
owner selections for S1, endpoints, and penalty treatment are recorded in the
decision log.

### Objective

Validate that the preferred New South Wales direction can support a compact, credible infrastructure-routing study using reproducibly accessible public data.

### Major Deliverables

- evidence-based recommendation for a compact Hunter / New England study area or a justified alternative within NSW;
- candidate fixed origin/destination scenarios tied to plausible infrastructure context;
- validated candidate sources for core constraints and contextual infrastructure;
- source-feasibility record covering access method, licensing, spatial coverage, attributes, format, CRS/resolution, stability, and automation implications;
- preliminary recommendation for the final 5–7 constraint components;
- identification of any source or methodological risks that could materially alter scope.

### Important Dependencies

- public source availability;
- ability to inspect or download sample data;
- authoritative NSW/Australian sources where practical;
- owner decision on final study/endpoints and consequential constraint choices after evidence is assembled.

### Broad Acceptance Criteria

- at least one viable compact NSW study scenario is supported by real accessible data;
- candidate endpoints create a non-trivial but manageable routing problem;
- every proposed core constraint has a credible, reproducible data source;
- fragile or legally ambiguous sources are rejected or clearly flagged;
- the owner can make the final study-area, endpoint, and constraint decisions from a concise evidence-based proposal.

## Priority 2 — Analytical Model Definition and Benchmarking

**Status:** Complete. The tested dependency-light core, approved sensitivity presets,
model documentation, synthetic benchmark, A* selection, and offline precomputed
static-MVP boundary are implemented.

### Objective

Turn the approved study scenario and sources into a transparent, testable routing methodology and resolve the runtime architecture through evidence.

### Major Deliverables

- approved final constraint set;
- explicit classification of hard exclusions, strong penalties, ordinary costs, and any justified preferences;
- documented normalization approach for each constraint;
- approved preset routing philosophies and weight configurations;
- defined project CRS and candidate grid resolution(s);
- benchmark of routing on a realistic cost grid;
- decision on A* versus Dijkstra or equivalent standard implementation;
- evidence-based choice between client-side, precomputed, or hybrid routing;
- defined route-assessment metrics supported by available data.

### Important Dependencies

- completion of Study and Data Feasibility;
- owner approval for consequential methodology choices;
- realistic sample datasets and a representative grid.

### Broad Acceptance Criteria

- the analytical model is transparent enough to explain to a non-specialist;
- normalization and weighting avoid false precision;
- routing respects exclusions and produces plausible deterministic/reproducible paths;
- route presets create meaningfully different trade-offs;
- routing architecture is selected using measured performance rather than preference alone;
- methodological assumptions and limitations are documented.

## Priority 3 — Reproducible Data and Routing Pipeline

**Status:** Active. Hydroline and the approved Copernicus GLO-30 S1 DEM are complete
and independently validated. SVTM REST capture remains partial after repeated
upstream failures; a guarded official bulk-package path for the same C2.0.M2.2
release is implemented, but its endpoint is currently WAF-challenged and its
analytical contents are unverified. The normalized-grid-to-route asset boundary and
disk-safe source acquisition boundary are implemented and tested. This milestone
still needs source-complete geographic derivation and must feed validated geographic
grids into that boundary.

### Objective

Implement the full offline Python workflow from source acquisition through route generation.

### Major Deliverables

- reproducible acquisition of approved datasets (Hydroline and Copernicus DEM
  complete; SVTM REST partial and official bulk delivery pending content verification);
- bounded persistent-storage acquisition with response/page/feature/storage limits,
  resumable page caches, and abandoned-cache cleanup;
- terrain-source selection using ELVIS/NSW as primary and Copernicus GLO-30 as the
  explicit fallback, with validated local artifact provenance;
- minimal repository and developer-tooling bootstrap for the approved workflow, including dependency/configuration manifests and an executable test entry point;
- study-area clipping and CRS/schema normalization;
- derivation of approved constraint layers;
- composite cost-surface generation;
- least-cost route assets for approved presets from validated geographic grids;
- provenance/configuration metadata;
- clear error handling for missing or invalid inputs;
- automated tests for core analytical logic.

### Important Dependencies

- approved analytical model;
- stable data access;
- chosen grid resolution and routing implementation.

### Broad Acceptance Criteria

- a clean environment can regenerate the core analytical outputs from documented public sources;
- a clean environment can install or execute the documented project tooling and run the available automated checks;
- failures are explicit rather than silently producing incomplete routes;
- normalization, cost combination, exclusions, and routing receive meaningful automated tests;
- generated routes are algorithmically genuine and reproducible under the same inputs/configuration;
- large raw source data is not committed without explicit justification.

## Priority 4 — Route Assessment and Application Assets

### Objective

Produce professional route-impact metrics, crossing inventories, and compact web-ready assets.

### Major Deliverables

- route length and approved terrain metrics;
- environmental intersection metrics supported by final datasets;
- watercourse, road, railway, and other approved crossing counts/details;
- route-comparison summary data;
- web-ready vector/raster/statistical assets;
- GeoJSON route output;
- CSV route-assessment/crossings output;
- validated metadata/provenance attached to final analytical outputs.

### Important Dependencies

- stable generated routes;
- final assessment schema;
- final constraint datasets.

### Broad Acceptance Criteria

- route assessment is independent of the composite routing score and uses understandable physical quantities where possible;
- geometry/intersection logic is covered by tests;
- application assets are compact enough for the intended deployment;
- outputs contain sufficient provenance to trace configuration and source versions.

## Priority 5 — Interactive Web Application

### Objective

Build a polished, map-led decision-support experience centered on route trade-offs.

### Major Deliverables

- React + TypeScript application;
- MapLibre map with study context, fixed endpoints, candidate route, and approved constraints;
- routing-strategy selection;
- route metrics and comparison views;
- selected crossing/feature inspection;
- responsive route updates according to the chosen routing architecture;
- restrained manual weighting controls if validated as usable and performant;
- clear preliminary-screening disclaimer and methodology explanation;
- responsive desktop/mobile behavior.

### Important Dependencies

- stable application-ready analytical assets;
- decision on routing execution architecture;
- approved product/visual direction if major choices arise.

### Broad Acceptance Criteria

- a non-specialist can understand what changes when the route strategy changes;
- the route remains visually dominant over contextual constraints;
- no generic GIS layer-control sprawl or excessive KPI/dashboard treatment is introduced;
- interactions are responsive enough to feel deliberate;
- the app communicates assumptions and limitations clearly;
- accessibility, responsiveness, and visual verification gates pass.

## Priority 6 — Professional Export Workflow

### Objective

Provide useful downstream outputs consistent with a consulting/engineering handoff.

### Major Deliverables

- working GeoJSON route export;
- working CSV assessment/crossings export;
- DXF route export if a lightweight reliable implementation remains justified;
- export metadata sufficient to identify route strategy/configuration.

### Important Dependencies

- stable route and assessment schemas;
- final decision on DXF feasibility.

### Broad Acceptance Criteria

- exported data opens correctly in representative downstream tools or validation libraries;
- exported geometry and attributes match the selected route and assessment;
- DXF does not introduce disproportionate complexity or unsupported CAD claims.

## Priority 7 — Validation, Documentation, Deployment, and Portfolio Readiness

### Objective

Bring the project from functional prototype to a credible public portfolio deliverable.

### Major Deliverables

- full quality-gate pass;
- methodology and source-data documentation;
- setup and regeneration instructions;
- documented limitations and professional-use disclaimer;
- optimized frontend and data payloads;
- public repository cleanup;
- static/predominantly static deployment;
- deployment verification;
- screenshots and supporting case-study material.

### Important Dependencies

- completion of analytical and frontend MVP;
- selected hosting target.

### Broad Acceptance Criteria

- repository and deployment can be reviewed without unsupported claims;
- a developer can understand how to regenerate the analysis;
- important analytical assumptions, sources, versions, and limitations are documented;
- tests/build/lint/type/data checks pass according to project tooling;
- deployed app behaves consistently with the validated local build;
- the final product looks and behaves like a small credible consulting deliverable rather than a coding demonstration.
