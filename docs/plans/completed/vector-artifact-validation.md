# Validate Acquired Vector Artifacts

## Objective

Add a reproducible, dependency-free integrity gate for external ArcGIS acquisition
manifests and per-layer artifacts before they enter future normalization or raster
derivation steps.

## Implemented

- Added `ico_model.vector_artifacts.validate_vector_manifest`.
- Added a CLI that checks the configured S1 scenario and analysis CRS, resolves
  relative artifact paths, and emits a compact validation report.
- Validated manifest/artifact schema, source and layer identity, output CRS, structural
  geometry, feature counts, object-ID completeness, and page-count arithmetic.
- Exported the validator from the package and added success and mismatch tests.

## Validation

- Standard-library tests: 39 passed.
- Compile, JSON, and whitespace checks passed.
- External road report: 46,092 features, one layer, EPSG:7856.
- External hydrography-area report: 12,652 features, one layer, EPSG:7856.
- Raw artifacts and reports remain outside Git under `/tmp`.

## Limits and follow-up

This validates capture integrity and structural geometry only. It does not establish
source licensing, spatial coverage, clipping, reprojection quality, rasterization,
analytical suitability, or hydrography-line availability. Source-schema normalization
and later GIS transformation remain future work.
