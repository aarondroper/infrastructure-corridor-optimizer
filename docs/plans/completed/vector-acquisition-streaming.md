# Stream Large Vector Acquisitions

## Objective

Remove the in-memory limitation from the bounded ArcGIS acquisition CLI so the large
hydrography and road layers can be captured safely into external build directories.

## Context

The object-ID-paginated adapter was verified with small deterministic tests and live
NPWS and railway captures, but the original CLI retained every feature in memory
before writing. Live ID discovery found approximately 68,320 hydrography-line and
46,092 road IDs in the S1 envelope.

## Implemented

- Added page callbacks to the existing validated object-ID acquisition loop.
- Added a staged streaming writer that writes each validated page directly to a
  temporary per-layer ArcGIS JSON file.
- Publish layer files and the compact manifest only after all selected layers pass.
- Reject non-empty output directories and remove staged files on validation failure.
- Kept the in-memory acquisition API for small deterministic tests.
- Added success and cleanup tests for the streaming writer.

## Acceptance and validation

- The CLI no longer accumulates already-written features in its acquisition bundle.
- CRS, transfer-limit, and geometry validation still runs for every page before it is
  written.
- A failed capture does not publish a manifest or leave staging output.
- Standard-library tests: 36 passed.
- Compile, JSON parsing, whitespace, and benchmark checks passed.
- Live streaming capture: NPWS Estate produced 20 polygon features in one complete
  page, with a valid manifest and EPSG:7856 artifact in `/tmp`.

## Limits and follow-up

The output remains ArcGIS JSON rather than normalized GeoJSON. Large captures may
still be slow or storage-heavy, and the vector data has not yet been clipped,
repaired, rasterized, or converted into cost surfaces. Full hydrography and road
captures were not attempted in this work unit; the next connected work is source
materialization where safe, followed by DEM/raster-vector derivation and aligned
grid construction.
