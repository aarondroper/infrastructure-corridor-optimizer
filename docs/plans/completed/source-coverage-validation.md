# Source Coverage Validation

## Objective

Extend Priority 3 source work from fixed endpoints to a reproducible metadata and
coverage probe for the configured public constraint-source candidates. Detect source
topology, CRS, geometry, and extent mismatches before downloading data, and surface
the elevation-source gap without silently selecting a replacement dataset.

## Context and approach

The implementation adds an ArcGIS metadata summarizer and schema guards for expected
layers, geometry types, layer names, and required layer types. The
`scripts/probe_sources.py` CLI probes configured ArcGIS sources, records CRS/extents/
topology, explicitly defers WMS, writes a machine-readable report, and returns a
non-zero status for failed source requirements. All logic is standard-library-only;
raw source data is not downloaded or committed.

## Validation

- `PYTHONPATH=src python3 -m unittest discover -s tests -v` — 20 tests passed.
- `PYTHONPATH=src python3 scripts/probe_sources.py --output /tmp/ico-source-probe.json --timeout 20` — completed against live public services.
- Live report validated GA, NPWS Estate, hydrography, and transport topology/CRS.
- Live report deferred SVTM WMS because a capabilities parser is not implemented.
- Live report failed the NSW Elevation candidate's required raster capability: it
  exposes SpotHeight, RelativeHeight, and Contour feature layers only.
- JSON parsing, whitespace, and Git checks passed for the implementation changes.

## Outcome

Completed on 13 September 2026. Priority 3 now has verified endpoint acquisition and
source-topology validation. A definitive terrain DEM source/path is intentionally
unresolved and requires owner input before geographic grid generation can claim
terrain coverage.

## Known limitations

- Service extents are metadata evidence, not proof that every tile/feature is complete
  inside the provisional processing envelope.
- SVTM WMS acquisition and all raw feature/raster downloads remain future work.
- Candidate source reprojection and aligned geographic grid derivation remain future
  work.
