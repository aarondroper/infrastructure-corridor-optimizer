# Bounded Vector Source Acquisition

## Objective

Extend Priority 3 from service-topology validation to reproducible acquisition of the
approved ArcGIS vector constraint sources: NPWS Estate, hydrography, roads, and
railways. Keep requests bounded to the provisional S1 envelope, request the project
analysis CRS, reject truncated responses, and write source-layer provenance outside
version control.

## Implemented

- Extended `ico_model.sources.ArcGISClient` with bounded envelope queries, explicit
  input/output CRS parameters, object-ID discovery, and integer-ID pagination.
- Added CRS and structural geometry guards for ArcGIS feature responses.
- Added configured layer IDs, geometry types, useful source attributes, service CRS
  metadata, and a 200-ID page size. The Named Watercourse group layer is represented
  by its queryable child layers 5 and 6.
- Added `scripts/acquire_vector_sources.py`, which validates service topology, acquires
  configured layers, writes per-layer ArcGIS JSON feature collections and a compact
  manifest, and supports source/component subsets for controlled runs.
- Added 7 tests covering query parameters, transfer limits, IDs, CRS/geometry guards,
  mocked acquisition output, and filtering.
- Updated architecture, feasibility, quality gates, and project state documentation.

## Validation

- `PYTHONPATH=src:. python3 -m unittest discover -s tests -v` — 34 tests passed.
- `PYTHONPATH=src python3 -m compileall -q src scripts tests` — passed.
- `python3 -m json.tool config/model.json` — valid JSON.
- Live NPWS capture succeeded: 20 polygon features in one complete page, written to
  `/tmp/ico-vector-npws`.
- Live railway capture succeeded: 415 polyline features in three complete pages,
  written to `/tmp/ico-vector-rail`.
- Full live acquisition was not retained: hydrography and road ID discovery reports
  large bounded volumes (68,320 and 46,092 IDs for the primary layers), so the
  in-memory bundle requires a later streaming-output refinement before attempting
  those large captures.

## Limits and follow-up

The adapter preserves ArcGIS JSON and does not clip, repair, rasterize, or calculate
intersections. SVTM WMS and terrain raster acquisition remain separate work. The next
connected work is a streaming or tiled external capture strategy for the large vector
layers, followed by schema normalization and aligned grid derivation.
