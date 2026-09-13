# Decisions

## Purpose

This file records consequential decisions that should persist across development sessions. It should not contain trivial implementation choices or unfinished proposals.

Where a decision depends on future evidence, record the unresolved question in `PROJECT_STATE.md` or `BACKLOG.md` rather than prematurely adding a decision here.

---

## D001 — Build an Infrastructure Corridor Optimizer

**Decision:** The project will be an Infrastructure Corridor Optimizer rather than a generic site-suitability application.

**Rationale:** Linear routing adds algorithmic GIS, infrastructure-planning trade-offs, crossing analysis, and engineering-oriented workflows that are not already strongly represented in the broader portfolio.

**Alternatives considered:** Generic renewable-energy or land-suitability analysis.

**Consequences:** The core analytical unit is a route/corridor between endpoints, not a ranked set of candidate areas. Scope and UX should remain centered on route trade-offs.

---

## D002 — Use New South Wales as the Default Geographic Direction

**Decision:** New South Wales, Australia is the default geographic direction, with Hunter / New England preferred for initial feasibility research.

**Rationale:** NSW provides geographic diversity relative to existing portfolio work and appears capable of supporting a plausible infrastructure/environmental routing study.

**Alternatives considered:** England, which had convenient data availability and inspired the original concept.

**Consequences:** England should not be reintroduced merely for convenience. A move away from NSW should occur only if source feasibility proves materially inadequate and should be treated as an owner-level scope decision.

---

## D003 — Treat the Product as Preliminary Corridor Screening

**Decision:** The product supports early-stage corridor screening, not detailed engineering or construction-ready route design.

**Rationale:** This keeps analytical claims credible and development scope aligned with a portfolio/consulting prototype.

**Consequences:** Documentation and UI must avoid engineering-approval claims. Detailed electrical, geotechnical, permitting, cadastral, field-investigation, and construction-access functions are outside scope.

---

## D004 — Use Weighted Least-Cost Routing

**Decision:** The core analytical model will use weighted least-cost routing.

**Rationale:** It is transparent, professionally recognizable, and well suited to combining multiple environmental and engineering constraints while making route trade-offs visible.

**Alternatives considered:** Novel optimization methods or a generic suitability score without route generation.

**Consequences:** Source layers must be transformed into compatible cost representations, assumptions must be explicit, and a standard routing algorithm such as A* or Dijkstra is sufficient.

---

## D005 — Limit the Core Model to Approximately 5–7 Major Constraints

**Decision:** The final routing model should use approximately 5–7 meaningful constraint components.

**Rationale:** This is sufficient to produce credible trade-offs without turning the project into an open-ended data-integration exercise.

**Consequences:** Additional layers need a clear analytical purpose. The final set remains an owner decision after source validation.

---

## D006 — Provide Approximately Three Understandable Route Strategies

**Decision:** The product should expose approximately three preset routing philosophies. Current conceptual names are Shortest, Balanced, and Environmental.

**Rationale:** Presets allow meaningful comparison without overwhelming the user with technical configuration.

**Consequences:** Route alternatives should primarily arise from different cost-weight configurations rather than unrelated algorithms. Exact naming and weights remain subject to methodological review and owner approval.

---

## D007 — Fix Two Endpoints for the Portfolio Implementation

**Decision:** The portfolio application will use two fixed route endpoints.

**Rationale:** Arbitrary project creation and endpoint selection add validation, UI, compute, and product complexity that are unnecessary for demonstrating the intended capabilities.

**Consequences:** The application remains a contained case study rather than a national routing service. Endpoint selection itself must still be evidence-based and plausible.

---

## D008 — Assess Routes with Physical Metrics

**Decision:** Candidate routes will be evaluated using understandable physical metrics in addition to any composite optimization cost.

**Rationale:** Professional users need to understand why routes differ, not merely see an abstract score.

**Consequences:** Where supported by final data, report measures such as kilometres, crossings, slope, and intersection length/area. Route assessment should be logically separable from route optimization.

---

## D009 — Make Data Ingestion and Preprocessing Reproducible

**Decision:** Source acquisition and geospatial preprocessing should be automated and reproducible.

**Rationale:** Data engineering is a core project objective, and hidden/manual desktop-GIS preprocessing would undermine reproducibility and portfolio credibility.

**Consequences:** Public sources, transformations, versions, and important configuration should be documented. Manual intervention should be minimized and explicit when unavoidable.

---

## D010 — Prefer Static or Predominantly Static Deployment

**Decision:** Deployment should be static or predominantly static unless evidence shows a backend is necessary.

**Rationale:** The project should remain free or extremely inexpensive to host and maintain.

**Consequences:** Heavy geoprocessing should generally occur during preprocessing. Client-side routing is acceptable if benchmarked performance is strong; otherwise routes may be precomputed.

---

## D011 — Use React, TypeScript, and MapLibre for the Web Application

**Decision:** The intended frontend stack is React + TypeScript with MapLibre for mapping.

**Rationale:** This supports the desired polished interactive geospatial experience and aligns with the broader portfolio's product-development capabilities.

**Consequences:** Major deviation from this stack requires a clear technical reason and should be treated as an architecture decision rather than an incidental implementation choice.

---

## D012 — Do Not Require PostGIS Without a Concrete Need

**Decision:** PostGIS is not part of the baseline architecture.

**Rationale:** The project should demonstrate technical judgement rather than introduce infrastructure solely for résumé coverage.

**Alternatives considered:** Database-backed geospatial architecture by default.

**Consequences:** Prefer file-based/offline processing unless a later requirement genuinely benefits from a spatial database. Introducing PostGIS as a fundamental dependency is an architecture decision.

---

## D013 — Include GeoJSON and CSV Exports

**Decision:** Route GeoJSON export and route-assessment/crossings CSV export belong in the intended workflow.

**Rationale:** They make the output more realistic as a consulting or engineering handoff.

**Consequences:** Export schemas should remain traceable to the selected route strategy and analytical configuration.

---

## D014 — Treat DXF Export as Desirable but Conditional

**Decision:** DXF export is preferred if it can be implemented reliably with low complexity, but it is not required for MVP success.

**Rationale:** DXF demonstrates awareness of GIS-to-CAD workflows but should not turn the project into a CAD-development effort.

**Consequences:** GeoJSON + CSV are sufficient if DXF proves disproportionate or unreliable. Omitting DXF after feasibility review does not constitute failure of the core project.

---

## D015 — Select Scenario S1

**Decision:** Use the Upper Hunter to Lake Macquarie / Eraring-area context as the
portfolio study scenario.

**Rationale:** The scenario creates a non-trivial corridor-screening problem across
the candidate terrain, environmental, hydrographic, road, and railway factors while
remaining tied to a public transmission-planning context.

**Consequences:** EnergyCo's published corridor remains contextual reference only;
the optimizer must generate and assess its own alternatives.

---

## D016 — Use Reproducible Public Energy Records as Endpoints

**Decision:** Use the current Geoscience Australia electricity records for Bayswater
and Eraring as the fixed endpoints. The selected records are object ID 251 for
Bayswater and object ID 286 for the 2,880 MW Eraring major-station record.

**Rationale:** Existing public, queryable records provide stable identifiers and
coordinates. They are more reproducible than inferring a proposed switching-station
location from a planning map.

**Consequences:** Source acquisition must revalidate identifiers and duplicate-feature
selection. The proposed Olney location remains contextual and is not treated as the
optimizer endpoint.

---

## D017 — Treat Environmental and Crossing Factors as Penalties

**Decision:** Model protected land, native vegetation, hydrography, roads, and
railways as weighted penalties and independent assessment metrics rather than
universal hard exclusions.

**Rationale:** The project is a preliminary screening tool and public mapped
indicators do not by themselves establish legal infeasibility for every corridor
cell. Penalties preserve visible alternatives and trade-offs.

**Consequences:** The model may return routes that require later permitting or
engineering review. Invalid or missing analytical inputs still make cells unavailable
so data-quality failures cannot be mistaken for low-cost land.

---

## D018 — Adopt Sensitivity Presets for the MVP

**Decision:** Adopt the `shortest`, `balanced`, and `environmental` profiles in
`config/model.json` as the MVP's approved sensitivity presets.

**Rationale:** The profiles provide three understandable trade-off views while
keeping the seven-component model and its assumptions explicit. They are intended for
comparative screening, not as objective weights or engineering standards.

**Consequences:** The profile values are stable configuration inputs for the initial
offline pipeline. Recalibration remains possible if real geographic outputs show that
the trade-offs are not meaningful; any materially different philosophy requires a new
reviewed decision.

---

## D019 — Precompute Routes for the Static MVP

**Decision:** Generate the approved sensitivity routes offline and ship compact route
and assessment assets to the static application. Defer arbitrary client-side weight
controls from the MVP.

**Rationale:** The measured A* benchmark supports efficient offline generation, while
no real geographic grid or browser benchmark yet justifies shipping a client-side
router and its larger payload/validation surface.

**Consequences:** The initial application will compare precomputed routes reliably on
static hosting. Interactive weighting may be reconsidered only through a future
owner-reviewed scope change backed by geographic and browser performance evidence.

---

## D020 — Use ELVIS/NSW DEM with a Copernicus GLO-30 Fallback

**Decision:** Use ELVIS/NSW elevation data as the primary terrain source and a dated
Copernicus DEM GLO-30 artifact as the explicit fallback for the S1 static MVP.

**Rationale:** The current NSW Elevation multi-CRS FeatureServer exposes point and
contour feature layers but no raster DEM. Geoscience Australia's ELVIS guidance
provides the appropriate discovery/order path for Australian elevation products,
while Copernicus GLO-30 provides a consistent lower-resolution fallback when the
preferred product is unavailable or does not cover the processing envelope.

**Consequences:** Configuration and provenance must identify the selected source and
artifact date. The pipeline may select the fallback only after the primary fails the
same local artifact checks for file availability, CRS metadata, resolution, complete
coverage, and nodata declaration. The current implementation validates sidecars; it
does not claim to download or process DEM pixels.
