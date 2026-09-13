# Generate Precomputed Route Assets

## Objective

Wire the approved sensitivity presets to the tested A* core through a reproducible
normalized-grid input contract and emit static route assets for the offline MVP.

## Outcome

Implemented `ico_model.precomputed_routes` and
`scripts/generate_precomputed_routes.py`. The implementation validates scenario,
analysis CRS, component coverage, rectangular grids, endpoints, and preset weights;
applies every configured preset with deterministic A*; and publishes one
provenance-rich JSON route asset per preset plus a portable manifest through a staged
output directory.

The asset contract is intentionally cell-based. It does not claim geographic routes,
select a final grid resolution, acquire terrain, derive raster/vector costs, or create
coordinates. Those remain the responsibility of the future GIS-backed grid stage.

## Validation

- 48 standard-library unit tests passed, including malformed context/grid/endpoint
  rejection and manifest publication tests.
- `PYTHONPATH=src:. python3 -m compileall -q src scripts tests` passed.
- Configuration JSON parsing and `git diff --check` passed.
- The CLI generated `shortest.json`, `balanced.json`, `environmental.json`, and
  `routes_manifest.json` from a deterministic temporary normalized-grid fixture.

## Follow-up

Continue with approved terrain acquisition and aligned raster/vector grid derivation.
Use this route generator only after real validated geographic inputs are supplied.
