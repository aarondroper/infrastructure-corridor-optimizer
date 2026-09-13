# Analytical Model

**Status:** Implemented dependency-light core with approved S1 sensitivity configuration

## Scope

The approved study direction is Scenario S1: an early-stage corridor screen between
the Bayswater area in the Upper Hunter and the Eraring area near Lake Macquarie. The
published Hunter Transmission Project corridor is contextual reference material,
not the optimizer's target or validation route.

The product remains a preliminary screening tool. A generated route is not a
construction, permitting, geotechnical, cadastral, or detailed electrical design.

## Approved source-backed endpoints

The current Geoscience Australia Electricity Infrastructure service is the source of
the fixed endpoint records. The model snapshot records:

| Role | Feature | Object ID | Capacity | Latitude | Longitude |
| --- | --- | ---: | ---: | ---: | ---: |
| Origin | Bayswater | 251 | 2,640 MW | -32.39525728 | 150.94913566 |
| Destination | Eraring | 286 | 2,880 MW | -33.06206226 | 151.52065341 |

The Eraring feature is the major 2,880 MW record among duplicate feature-name
results. The exact identifiers, global IDs, locality, state, status, source snapshot,
and coordinate reference systems are in `config/model.json`; source acquisition must
revalidate them before generating derived assets.

## Cost components

The approved sensitivity model uses seven interpretable components:

1. base movement/route length;
2. DEM-derived terrain difficulty, initially represented by slope;
3. NPWS protected or managed land;
4. SVTM native-vegetation sensitivity;
5. hydrography and water-area crossings;
6. road crossings;
7. railway crossings.

Length is the ordinary base cost. The other six components are weighted penalties,
not universal hard exclusions. This preserves route alternatives for a screening
comparison while avoiding the unsupported claim that a public indicator alone proves
legal infeasibility. Missing or non-finite analytical inputs remain unavailable cells
so incomplete data cannot silently produce a plausible route.

## Normalization and combination

The current configuration is explicit and approved for sensitivity comparison; the
source-derived transformations remain provisional until geographic coverage and data
quality are validated:

- slope is linearly clamped from 0 to 20 degrees to [0, 1];
- binary indicator surfaces use 0 outside and 1 inside the mapped feature;
- crossings use source feature-class mappings and are independently counted during
  route assessment;
- component grids are combined as a non-negative weighted sum;
- optional hard-exclusion cells are supported by the core API but are not enabled by
  the approved S1 penalty policy.

The `shortest`, `balanced`, and `environmental` profiles in `config/model.json` are
approved sensitivity presets for the MVP. They sum to one and cover the same seven
components so their route trade-offs can be compared without changing the model
schema. They remain planning assumptions rather than objective or engineering truths,
and should be recalibrated only if geographic validation shows that the resulting
trade-offs are not meaningful.

## Routing core

`src/ico_model/routing.py` provides deterministic eight-neighbor least-cost routing
with orthogonal distance 1 and diagonal distance √2. The edge cost is the average of
the adjacent cell costs multiplied by movement distance. Infinite cells are
unavailable, and diagonal moves cannot cut between two blocked orthogonal corners.
The API reports the route cells, total cost, and explored-cell count.

The benchmark uses deterministic synthetic penalty landscapes at 128², 256², and
512². A* and Dijkstra returned the same costs and path lengths. A* explored 8,023 vs
16,281 cells at 128², 27,635 vs 65,032 at 256², and 111,200 vs 260,119 at 512²;
the recorded wall-clock results are in `benchmarks/results.json`. A* explored 51–57%
fewer cells and was 35–50% faster in these runs. This supports A* as the current
offline routing implementation. It does not establish browser capacity, geographic
route quality, or a final grid resolution.

## Execution boundary

The approved MVP direction is precomputed routes for a static application:
generate a small number of reviewed profiles offline and ship compact route/metric
assets. Client-side arbitrary weighting should remain deferred until a real derived
grid and browser benchmark show that it is responsive and useful. A smaller hybrid
client grid is not part of the approved MVP, but could be considered through a future
owner-reviewed scope change.

## Independent route assessment

The composite cost is not the only output. Each route should later report physical or
countable measures supported by the selected sources: length, terrain statistics,
protected-land overlap, native-vegetation overlap, watercourse crossings, road
crossings by class, and railway crossings. These metrics explain trade-offs and must
not be inferred solely from the composite score.

## Implementation boundary

The current Python core intentionally has no GIS dependency. It validates normalized
rectangular grids, combines layers, and routes them. Priority 3 now has a standard-
library ArcGIS acquisition boundary for the fixed GA endpoint records; it still needs
source adapters/coverage checks for the remaining components, clipping/reprojection,
raster/vector derivation, route assessment, and generated web assets.
