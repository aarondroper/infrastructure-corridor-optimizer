# Source Acquisition Bootstrap

## Objective

Begin Priority 3 by implementing a reproducible, dependency-light source-acquisition
boundary for the approved S1 endpoint records. The slice validates live ArcGIS service
access and endpoint identity without committing raw external data or silently
promoting provisional raster-source choices to final decisions.

## Context and approach

S1 and the Bayswater/Eraring endpoint convention were approved. The implementation
adds a standard-library-only ArcGIS REST JSON client with bounded requests, explicit
user-agent and timeout handling, service CRS validation, endpoint identity checks,
and atomic provenance-manifest output. Fixture-backed tests cover successful parsing,
HTTP failures, CRS mismatch, missing records, and identity mismatch. Raw external data
is excluded from version control.

## Validation

- `PYTHONPATH=src python3 -m unittest discover -s tests -v` — 19 tests passed.
- `PYTHONPATH=src python3 scripts/acquire_sources.py --output /tmp/ico-source-manifest.json --timeout 20` — live GA endpoint acquisition succeeded.
- The manifest contained the configured EPSG:7844 service, source metadata, query,
  Bayswater object ID 251, and Eraring object ID 286.
- JSON parsing, inventory, and trailing-whitespace checks passed.
- Git status/diff checks passed once Git was initialized.

## Outcome

Completed on 13 September 2026. Priority 3 now has a verified endpoint acquisition
slice and minimal Python package metadata. The next work is acquisition and coverage
validation for the remaining terrain, protected-land, native-vegetation, hydrography,
road, and railway inputs, followed by aligned geographic grids and offline route
generation.

## Known limitations

- The live command validates endpoint acquisition only; it does not download or derive
  the full geographic constraint stack.
- Source identifiers and schemas may change and must be revalidated on acquisition.
- No raw source data or geographic route assets are committed.
