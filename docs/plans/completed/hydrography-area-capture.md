# Capture Hydrography Area Layer

## Objective

Materialize the smaller configured hydrography-area layer independently while keeping
the stalled full hydrography-line capture explicitly unresolved.

## Outcome

- The live service’s sparse root topology was resolved through child-layer detail
  metadata without weakening validation.
- The staged CLI published 12,652 hydrography-area object IDs and 12,652 features in
  64 complete pages using the global 200-ID page size.
- The external artifact is 15.8 MB, declares EPSG:7856, parses as JSON, matches its
  manifest count, and left no staging directory.
- The full hydrography-line layer remains unresolved: its earlier 68,320-ID capture
  stalled during a later page and was interrupted with no published output.

## Validation

- `PYTHONPATH=src:. python3 -m unittest discover -s tests -v` — 37 tests passed.
- Configuration JSON parsing and `git diff --check` passed.
- Raw artifacts remain outside Git under `/tmp`.

## Limits and follow-up

This does not resolve hydrography-line capture, terrain/SVTM acquisition, or any
vector-to-raster derivation. The line-layer service behavior remains an external
performance/availability boundary; do not weaken CRS, transfer-limit, geometry, or
staged-publication validation to bypass it.
