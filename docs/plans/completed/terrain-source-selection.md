# Terrain Source Selection and Artifact Contract

## Objective

Implement the approved terrain-source policy for Priority 3: use ELVIS/NSW DEM data
as the primary source and a dated Copernicus DEM GLO-30 artifact as the explicit
fallback. Add a dependency-light artifact contract so the future raster pipeline can
reject missing, partial, or out-of-envelope terrain inputs before slope derivation.

## Context

- The current NSW Elevation multi-CRS FeatureServer is reachable but exposes only
  SpotHeight, RelativeHeight, and Contour feature layers, not a raster DEM.
- The owner approved ELVIS/NSW as primary and Copernicus GLO-30 as fallback.
- ELVIS acquisition is a portal/order/download workflow; the repository must record
  source and artifact provenance without claiming automated download where none is
  verified.
- The analysis envelope and target analysis CRS are present in `model.json`.

## Implemented

- Replaced the blocked active elevation candidate with explicit `elvis-nsw-dem` and
  `copernicus-dem-glo-30` source records and an ordered terrain-source policy.
- Added `ico_model.terrain` sidecar loading, local-file and metadata validation, and
  primary/fallback selection with an auditable selection report.
- Added `scripts/select_terrain_source.py`; raw DEM files and sidecars remain outside
  version control.
- Added unit and subprocess coverage for primary selection, fallback selection,
  envelope/CRS/resolution/nodata/file checks, relative paths, and CLI output.
- Recorded decision D020 and reconciled the feasibility, architecture, analytical
  model, backlog, and project-state documents.

## Validation

- `PYTHONPATH=src python3 -m unittest discover -s tests -v` — 27 tests passed.
- `PYTHONPATH=src python3 benchmarks/benchmark_routing.py --sizes 128 256 512` —
  completed; A* and Dijkstra retained equal path costs and A* explored fewer cells
  at every size.
- `PYTHONPATH=src python3 scripts/probe_sources.py --output <temporary report>
  --timeout 20` — live probe validated GA, NPWS, hydrography, and transport; ELVIS
  and Copernicus were recorded as deferred portal/data-access sources; no failures.
- `python3 -m json.tool config/model.json` — valid JSON.
- The CLI success path is exercised by the automated test with temporary sidecars
  and a local artifact placeholder; no external DEM download is claimed.

## Limits and follow-up

This slice does not download DEM tiles, inspect GeoTIFF pixels, reproject rasters,
derive slope, or validate a real DEM's geographic coverage. The next work unit is to
implement bounded acquisition or import handling for the selected source artifacts,
then derive and validate aligned terrain grids alongside the remaining constraints.
