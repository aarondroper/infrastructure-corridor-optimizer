# Analytical Model Definition and Benchmarking

## Objective

Translate the approved S1 study direction into an explicit, testable analytical
configuration and use representative grid benchmarks to choose a defensible routing
execution direction for the preliminary screening MVP.

## Approved context

- Scenario S1: Upper Hunter to Lake Macquarie / Eraring-area corridor context.
- Origin: current Geoscience Australia electricity record `Bayswater`, object ID 251.
- Destination: current Geoscience Australia electricity record `Eraring`, object ID
  286, selected from duplicate Eraring records because it is the 2,880 MW major station
  record.
- Constraint families: length, terrain, protected land, native vegetation,
  hydrography, roads, and railways.
- Environmental and crossing factors are penalties/assessment metrics, not universal
  hard exclusions.

## Approach

1. Add a standard-library-only model core for source-backed endpoints, component
   provenance, normalization, penalties, and sensitivity profiles.
2. Add tested cost normalization, weighted cost combination, and deterministic A*
   routing primitives suitable for reuse by the later geospatial pipeline.
3. Benchmark A* and Dijkstra on deterministic synthetic grids approximating compact
   raster routing workloads at 128², 256², and 512² cells.
4. Document the normalization/penalty philosophy, benchmark results, limitations, and
   the precomputed-versus-client execution boundary.

## Acceptance criteria

- Approved endpoints and source provenance are explicit and uniquely identifiable.
- Cost transformations and penalty semantics are documented and covered by tests.
- Routing handles diagonal movement, exclusions, deterministic ties, and no-path cases.
- Benchmark results are reproducible and report runtime, explored cells, and path cost.
- The approved sensitivity profiles are clearly separated from objective or engineering claims.

## Validation

- `PYTHONPATH=src python3 -m unittest discover -s tests -v` — 12 tests passed.
- `PYTHONPATH=src python3 benchmarks/benchmark_routing.py --sizes 128 256 512` — completed for all six combinations.
- JSON parsing, inventory, and trailing-whitespace checks passed.
- Git status/diff checks were attempted; the workspace exposes unusable Git metadata.

## Outcome

Completed on 13 September 2026. The owner approved the three sensitivity profiles
and offline precomputed routes for the static MVP. A* is selected for offline route
generation based on the synthetic benchmark. Priority 3 is the next work unit:
source acquisition, coverage validation, geographic grid derivation, and route asset
generation.

## Risks carried forward

- Synthetic grids are a performance proxy, not evidence of final geographic route
  quality or browser performance.
- Sensitivity profiles are planning assumptions and may require recalibration after
  geographic validation.
- Public source identifiers and schemas may change; endpoint validation remains part
  of source acquisition.
- The standard-library core does not replace the geospatial libraries required by the
  later data pipeline.
