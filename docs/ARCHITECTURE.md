# Architecture

## Status of This Document

This document separates the repository's **verified architecture** from the **intended architecture**. Planned components are not evidence that corresponding files, services, modules, or deployments exist.

## Architectural Goals

The architecture should support:

- reproducible ingestion of multiple public geospatial sources;
- transparent conversion of heterogeneous source layers into routing constraints;
- weighted least-cost routing between two fixed endpoints;
- route-impact and crossing assessment;
- compact web-ready analytical outputs;
- fast interactive route comparison;
- free or extremely inexpensive deployment;
- clear provenance and method documentation;
- minimal permanent infrastructure.

The preferred high-level pattern is:

`public data sources -> offline Python build pipeline -> compact derived assets -> lightweight React/MapLibre application`

## Verified Existing Architecture

The repository currently contains governance and feasibility documentation plus a
dependency-light analytical core under `src/ico_model/`, approved sensitivity model configuration,
unit tests, a minimal Python package manifest, an ArcGIS endpoint acquisition module,
and a deterministic benchmark. The implemented core validates and combines normalized
grids, runs deterministic eight-neighbor A*/Dijkstra routing, and validates a live
Geoscience Australia endpoint snapshot. There are still no geographic cost surfaces,
frontend files, build/deployment configuration, or generated routes.

The sections below distinguish implemented analytical behavior from intended pipeline
and application components. They become verified only when implemented files and
reproducible validation provide evidence.

## Intended Languages and Frameworks

### Processing / analysis

**Language:** Python

Likely geospatial and numerical libraries:

- GeoPandas;
- Rasterio;
- GDAL;
- NumPy;
- Shapely.

Routing may use one of:

- a small purpose-built A* implementation;
- Dijkstra or A* from an established library;
- NetworkX;
- scikit-image;
- another standard transparent implementation appropriate to the final raster/grid representation.

The routing implementation should favor explainability, correctness, deterministic behavior where practical, and manageable dependencies over novelty.

### Frontend

**Languages/frameworks:** React + TypeScript

**Map rendering:** MapLibre

The app should be map-led and should expose route strategy, selected constraints, route statistics, crossing/impact detail, and exports without becoming a general GIS interface.

## Intended Application Components

The exact source tree is not yet established. The logical components below should guide implementation but should not be treated as required directory names.

### 1. Source acquisition layer

Responsibilities:

- retrieve or access public NSW/Australian and other approved datasets;
- record source URLs/services, versions/dates where available, licensing/provenance, and acquisition metadata;
- fail clearly when required data cannot be obtained or validated;
- avoid embedding unnecessary manual preprocessing steps.

The implemented `ico_model.sources` module currently covers bounded ArcGIS REST JSON
requests, service CRS validation, endpoint identity validation, and ArcGIS metadata
topology guards. The CLIs in `scripts/acquire_sources.py` and
`scripts/probe_sources.py` write small provenance and source-topology reports.
`ico_model.vector_artifacts` and `scripts/validate_vector_artifacts.py` validate
external acquisition manifests and per-layer artifacts before downstream processing.
`ico_model.vector_schema` provides explicit, source-preserving canonical aliases for
all seven configured vector components; it does not assign analytical costs or
weights.
`ico_model.terrain` and `scripts/select_terrain_source.py` validate local DEM sidecars
and select the configured ELVIS/NSW primary or Copernicus GLO-30 fallback with
provenance. Actual portal acquisition, raster-pixel reading, and reprojection remain
future work; the selected source policy does not claim those operations are complete.
`scripts/acquire_vector_sources.py` now provides bounded, object-ID-paginated ArcGIS
acquisition for the NPWS, SVTM native-vegetation, hydrography, road, and railway layers, requesting EPSG:7856
output and rejecting incomplete pages. Its CLI streams validated pages to staged
external per-layer ArcGIS JSON feature collections and publishes a compact manifest
only after the selected capture completes; the module also retains an in-memory API
for small deterministic tests. The configured road layer uses a 150-ID page size
because the live transport service rejected the 200-ID default, while the global
default remains 200. It does not clip, repair, rasterize, or derive cost surfaces.
Terrain raster acquisition remains future work; the SVTM WMS resource is retained for
display rather than analytical capture.
The SVTM ArcGIS feature-layer resource is configured for native-vegetation capture;
its WMS resource remains available for display. The configured S1 envelope contains
approximately 216,808 intersecting polygons, so full materialization remains an
external operational task and is not treated as verified output.
`ico_model.precomputed_routes` and `scripts/generate_precomputed_routes.py` provide
the offline grid-to-route execution boundary: they validate a seven-component
normalized-grid bundle, apply each approved preset, run deterministic A*, and publish
provenance-rich route-cell assets. They do not derive geographic grids or coordinates.

### 2. Study-area preparation

Responsibilities:

- define the selected compact NSW study area;
- define the two approved fixed route endpoints;
- establish the project CRS;
- clip or subset source data consistently;
- validate required spatial coverage.

Scenario S1 and the public Bayswater/Eraring endpoint records are selected. The
processing envelope and endpoint validation remain configuration inputs and must be
checked against each source snapshot.

### 3. Constraint derivation

Responsibilities:

- convert approved source datasets into approximately 5–7 interpretable routing components;
- separate hard exclusions, high penalties, ordinary costs, and any justified preference/incentive surfaces;
- normalize heterogeneous variables onto compatible cost representations;
- document transformation assumptions and units;
- preserve enough metadata for provenance.

Potential constraint families include:

- distance/base movement cost;
- terrain/slope;
- protected areas;
- native vegetation/woodland;
- watercourses;
- roads;
- railways;
- developed/urban land;
- existing infrastructure proximity;
- flood-prone land if source feasibility and analytical value justify it.

The current draft set is length, terrain, protected land, native vegetation,
hydrography, roads, and railways. The owner approved penalty treatment for the
environmental and crossing components; exact transformations and weights remain
subject to validation.

### 4. Composite cost model

Responsibilities:

- combine normalized constraint components using explicit configuration;
- enforce approved hard exclusions;
- support a small number of understandable routing presets;
- preserve weights and configuration as versioned analytical inputs;
- avoid hidden transformations or false precision.

The current sensitivity presets are:

- Shortest;
- Balanced;
- Environmental.

The values are approved sensitivity assumptions, not objective or engineering truths.

### 5. Routing engine

Responsibilities:

- calculate a genuine least-cost route between the two fixed endpoints;
- use a standard transparent algorithm such as A* or Dijkstra;
- respect hard exclusions;
- expose deterministic or reproducible behavior where practical;
- provide enough diagnostics to detect disconnected endpoints or invalid cost surfaces.

Grid resolution must be selected through benchmarking of analytical quality, preprocessing cost, and browser/runtime performance.

### 6. Route assessment

Responsibilities:

- evaluate each generated route independently of the composite routing score;
- calculate understandable physical metrics supported by the final data;
- identify route crossings and affected features;
- produce machine-readable summaries for the application and exports.

Candidate metrics include:

- total route length;
- elevation and terrain characteristics;
- maximum or representative slope;
- protected-area intersection;
- native vegetation or woodland intersection;
- watercourse crossings;
- major-road crossings;
- railway crossings;
- flood-prone land intersection if retained.

### 7. Web asset generation

Responsibilities:

- convert analytical outputs into compact static assets;
- create GeoJSON, JSON, CSV, raster/grid, or optimized vector assets as appropriate;
- minimize application payload and fragile runtime dependencies;
- include metadata needed for provenance and UI explanation.

Potential formats include:

- GeoJSON;
- JSON;
- CSV;
- compact raster/grid representations;
- PMTiles or equivalent optimized vectors if justified;
- DXF for route export if retained.

### 8. Frontend application

Responsibilities:

- render the study landscape and approved contextual/constraint layers;
- display the fixed endpoints and selected candidate route;
- allow route-strategy switching;
- present route summary metrics and route comparisons;
- allow feature/crossing inspection;
- expose a restrained number of high-level weighting controls if supported by the routing architecture;
- export the selected route and route assessment;
- communicate methodology and preliminary-screening limitations clearly.

## Routing Execution Architecture

The implemented routing core is Python A* with a Dijkstra comparison path. A
deterministic synthetic benchmark supports A* for offline generation, but it does not
select a browser architecture or a final geographic grid resolution.

### Option A — client-side routing

A compact cost grid is shipped with the application and A* or equivalent runs in a Web Worker.

**Advantages**

- genuinely interactive weight changes;
- no server requirement;
- strong demonstration of algorithmic GIS.

**Risks**

- browser memory use;
- CPU cost;
- grid-size constraints;
- more complex client validation.

### Option B — precomputed routing

The build pipeline generates the small set of approved preset routes.

**Advantages**

- robust static deployment;
- minimal browser compute;
- small operational surface.

**Trade-off**

- weaker interactive weighting story.

### Hybrid possibility

Preset routes can be precomputed while optional user weighting uses a smaller client-side grid if benchmarking supports it.

**Decision status:** The approved MVP direction is offline precomputed routes, because
it matches the static deployment preference and keeps unvalidated browser compute out
of scope. User-controlled weighting is deferred from the MVP and would require a
future owner-reviewed scope change. See
`docs/ANALYTICAL_MODEL.md` and `benchmarks/results.json`.

## Storage and Data Model

### Raw data

Large raw source datasets should live outside version control, acquired reproducibly from documented public sources or cached in a controlled local/build location.

### Configuration

Analytical configuration should be explicit and version-controlled, including where applicable:

- study area;
- endpoints;
- CRS;
- grid resolution;
- selected constraints;
- normalization parameters;
- exclusions;
- route preset weights;
- source metadata/version identifiers.

### Derived data

Derived artifacts should be separated conceptually into:

- intermediate analytical data;
- reproducible final analytical outputs;
- frontend-ready assets.

Repository policy for committing derived artifacts should be decided based on size, reproducibility, and deployment needs. Generated artifacts should not be committed by default merely for convenience.

### Database

PostGIS is **not part of the current intended baseline architecture**. Introduce it only if later evidence shows it solves a concrete requirement better than file-based processing.

## APIs

No permanent application API is currently required.

The preferred deployment model avoids a backend where possible. External data APIs/services may be used during acquisition/build steps, but the production application should minimize runtime dependence on external GIS services.

If a backend becomes necessary, that would be a consequential architecture change and should be documented as a decision before implementation.

## External Dependencies and Data Sources

The repository now has a feasibility-validated candidate source stack, but no source
has yet become definitive because study geography, endpoints, and the final constraint
set remain owner decisions. The detailed evidence is in
`docs/STUDY_AND_DATA_FEASIBILITY.md`.

Feasibility-validated candidates include:

- Geoscience Australia Electricity Infrastructure for public energy assets and
  high-voltage lines;
- NSW Spatial Services multi-CRS Transport and Elevation services;
- NSW Hydrography;
- NSW NPWS Estate;
- NSW State Vegetation Type Map;
- EnergyCo Hunter project pages and boundary data for study context only.

Preferred source ecosystems include:

- NSW government electricity/transmission/open-data services;
- NSW Spatial Services and other state geospatial sources;
- Australian or NSW protected-area/environmental datasets;
- Copernicus DEM or an appropriate Australian/NSW elevation product;
- authoritative NSW/Australian road and rail data where practical, with OpenStreetMap/Geofabrik acceptable when substantially simpler and reproducible;
- NSW/Australian hydrography where practical;
- Australian/NSW vegetation or land-cover data where ecological interpretation is sufficiently clear;
- a flood-prone-land source only if access, relevance, and analytical value are strong enough.

Before a source becomes part of the definitive architecture, validate:

- access method;
- licensing;
- coverage;
- useful attributes;
- CRS/resolution;
- data quality;
- stability;
- processing footprint;
- suitability for automated ingestion.

Substituting an approved important dataset with a materially different source is an owner decision boundary.

## Deployment Architecture

The intended deployment is static or predominantly static.

Preferred characteristics:

- frontend served from inexpensive static/edge hosting;
- analytical outputs produced during build/preprocessing;
- no always-on GIS server;
- no paid service dependency unless explicitly approved;
- application capable of functioning from compact versioned web assets.

A specific hosting provider has not been selected.

## Important Technical Boundaries

- This is a single-study portfolio product, not a configurable national routing service.
- Endpoints are fixed for the portfolio implementation.
- Heavy geoprocessing belongs offline unless benchmarking clearly justifies client execution.
- One standard routing algorithm is sufficient.
- The routing model should remain transparent and explainable.
- Do not introduce PostGIS, microservices, backend APIs, queues, or other infrastructure solely for résumé breadth.
- Do not imply construction-level engineering validity.
- Methodological assumptions must remain explicit and separable from source data.
