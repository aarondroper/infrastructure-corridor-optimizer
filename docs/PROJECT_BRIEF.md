# Project Brief

## Project Identity

**Name:** Infrastructure Corridor Optimizer

**Project type:** Self-directed portfolio / consulting showcase project.

**Geographic direction:** New South Wales, Australia. Scenario S1 is selected: an
Upper Hunter to Lake Macquarie / Eraring-area screening context using the public
Bayswater and Eraring records as fixed endpoints. The exact processing envelope and
source coverage still require implementation validation.

**Current phase:** First geographic and static-MVP execution slice. The repository has
a tested dependency-light cost/routing core, approved sensitivity configuration,
validated S1 source artifacts, a real 100 m geographic grid, offline routes,
feature-level assessments, compact application assets, and a local React/TypeScript
+ MapLibre build. See `docs/PROJECT_STATE.md` for the evidence-backed snapshot.

## Purpose

The project is a geospatial decision-support application for identifying and comparing plausible early-stage infrastructure corridors between two fixed locations. It should balance route length, terrain, environmental sensitivity, infrastructure crossings, and other spatial constraints in a transparent weighted least-cost model.

The representative planning question is:

> Where is a plausible preliminary corridor between an infrastructure origin and destination when route length, engineering difficulty, environmental sensitivity, and difficult crossings all need to be considered?

A representative use case is preliminary routing of an underground transmission cable, power connection, utility corridor, or comparable linear infrastructure.

This is an **early-stage screening** tool. It is not a detailed engineering or construction design system.

## Intended User / Client Problem

The target audience is an infrastructure, energy, transmission, utilities, engineering, environmental-planning, or geospatial consultancy performing preliminary corridor screening and feasibility assessment.

The user needs to compare plausible corridors and understand trade-offs, rather than receive a single unexplained optimized line. The application should make it clear why route alternatives differ and what consequences each introduces.

## Primary Use Cases

1. View a contained infrastructure-routing study with two fixed endpoints.
2. Compare a small number of preset routing strategies, initially conceived as Shortest, Balanced, and Environmental.
3. Inspect how routing geometry responds to different constraint importance.
4. Compare route length, terrain difficulty, environmental impacts, and difficult crossings using understandable physical metrics.
5. Toggle or inspect key contextual and constraint layers.
6. Inspect crossings or affected features in more detail.
7. Optionally adjust a small number of high-level weights if performance and usability permit.
8. Export the selected route and route assessment for downstream use.

## Intended Deliverable

The finished project should include:

- a reproducible Python geospatial ingestion and preprocessing pipeline;
- a transparent weighted least-cost routing model;
- candidate routes for the principal strategy presets;
- route-level impact and crossing assessment;
- compact application-ready data products;
- a polished React + TypeScript + MapLibre web application;
- GeoJSON route export;
- CSV assessment/crossings export;
- DXF route export if it is inexpensive and reliable enough to justify inclusion;
- automated tests for important analytical logic;
- methodology, data-source, provenance, limitation, setup, and development documentation;
- a public deployment using free or extremely inexpensive infrastructure;
- a clean public repository and enough polished material to support a consulting/portfolio case study.

## Portfolio / Business / Product Goals

The project exists to demonstrate professional capability across a domain not already strongly represented elsewhere in the portfolio.

It should showcase:

- algorithmic GIS and least-cost routing;
- environmental and infrastructure constraint modelling;
- raster/vector integration;
- reproducible geospatial data engineering;
- Python analytical software engineering;
- route-impact and crossing analysis;
- GIS-to-engineering handoff awareness;
- MapLibre-based interactive geospatial product development;
- product and consulting judgement in translating a loosely defined planning question into a defensible analytical workflow.

The final result should feel like a small credible consulting engagement, not a routing tutorial or generic GIS demonstration.

## In-Scope Capabilities

The intended MVP includes approximately:

- one contained NSW study area;
- two fixed infrastructure endpoints;
- 5–7 meaningful constraint components;
- a weighted least-cost routing model;
- clear distinction between hard exclusions, strong penalties, ordinary weighted costs, and potentially preferred areas where methodologically justified;
- one standard robust routing algorithm such as A* or Dijkstra;
- approximately three understandable preset routing strategies;
- route-level assessment using physical metrics where possible;
- interactive map visualization and route comparison;
- constraint inspection;
- responsive updates when route strategy changes;
- limited manual weighting controls if understandable and performant;
- reproducible source acquisition and preprocessing;
- lightweight static or predominantly static deployment;
- professional data exports.

The current draft analytical components are distance, slope, protected land, native
vegetation/woodland, watercourses, roads, and railways. Environmental and crossing
components are weighted penalties and assessment metrics rather than universal hard
exclusions. Additional layers such as developed land or flood-prone land remain
optional future scope.

## Explicit Non-Goals

The project is not intended to become:

- a construction-ready infrastructure routing system;
- a detailed electrical-engineering design tool;
- a geotechnical design system;
- a national routing engine;
- a general-purpose infrastructure planning platform;
- a multi-project SaaS product;
- an environmental-impact-assessment platform;
- a permitting workflow;
- a cadastral or property-rights negotiation tool;
- a detailed construction-access model;
- a real-time operational system.

The MVP should not include:

- authentication, user accounts, or billing;
- arbitrary project creation;
- arbitrary user-uploaded datasets;
- arbitrary national endpoint selection;
- expensive permanent GIS infrastructure;
- unnecessary microservices;
- detailed engineering design rules;
- optimization research beyond what is needed for a robust explainable route;
- unnecessary ML/AI features.

## Important Constraints

### Product and scope constraints

- The project remains a single contained study.
- The two route endpoints are fixed in the portfolio implementation.
- The MVP should remain close to 5–7 constraints, three routing strategies, one core routing algorithm, route assessment, and lightweight exports.
- The application must clearly state that outputs support preliminary corridor screening only.

### Data constraints

- Use public/open datasets.
- Prefer authoritative NSW/Australian sources where practical.
- Source ingestion should be programmatic or automatable.
- Manual desktop-GIS preprocessing should be minimized.
- Large raw datasets should not be committed to the repository.
- Runtime dependence on fragile external GIS services should be minimized.
- Data selection should favor stable access, manageable licensing, useful provenance, and suitability for a compact study area.

### Technical constraints

- Python is the intended processing language.
- React + TypeScript + MapLibre are the intended frontend stack.
- Heavy geoprocessing should occur during preprocessing where practical.
- Static or predominantly static deployment is strongly preferred.
- PostGIS is not required unless a concrete need emerges.
- Client-side routing is preferred only if a realistic grid benchmark shows it is responsive and memory-efficient; otherwise precomputed routing is acceptable.

### Methodological constraints

- The analysis should avoid false precision.
- Weighting assumptions must be documented as planning assumptions rather than objective truth.
- Consequential choices about constraints, exclusions, and weighting philosophy require owner review.
- Route assessment should use understandable physical quantities instead of relying only on a composite cost score.

## Definition of Overall Project Success

The project is successful when a user can open a polished application, understand a plausible infrastructure-routing problem, compare clearly different corridor strategies, inspect the environmental and engineering trade-offs behind those routes, and export useful route information.

The underlying routes must be algorithmically genuine and generated from a reproducible pipeline using real public data. The methodology must distinguish source facts from assumptions, document provenance and transformations, and avoid implying construction-level validity.

Professionally, the project should convincingly demonstrate:

- environmental and infrastructure GIS;
- automated multi-source spatial data ingestion;
- raster/vector processing;
- weighted spatial modelling;
- least-cost routing;
- route-impact analysis;
- engineering-oriented export workflows;
- modern interactive MapLibre product development;
- reproducibility, testing, and documentation;
- restrained professional cartography and UX judgement.
