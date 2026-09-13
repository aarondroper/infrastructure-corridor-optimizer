# Define Canonical Vector Schema

## Objective

Create a dependency-free, source-preserving normalization boundary for validated
ArcGIS features so later rasterization and route assessment do not depend on each
service’s attribute spelling.

## Implemented

- Added explicit component-specific aliases for all seven configured vector
  components: protected land, three hydrography line variants, hydrography area,
  roads, and railways.
- Added case-insensitive source attribute handling and integer source-object-ID
  normalization.
- Preserved original source attributes and geometry in every canonical feature.
- Carried source ID, layer, CRS, envelope, and query provenance through canonical
  feature collections.
- Added tests for schema coverage, alias normalization, provenance, and missing IDs.

## Validation

- Standard-library tests: 43 passed.
- Compile, JSON, and whitespace checks passed.
- Real external artifacts normalized successfully: 46,092 road features and 12,652
  hydrography-area features, each with unique stable IDs and EPSG:7856 provenance.

## Limits and follow-up

This is schema normalization only. It does not validate geometric validity beyond the
existing artifact gate, reproject, clip, rasterize, derive slope, or assign analytical
cost values. Those GIS transformations and the unresolved hydrography-line capture
remain future work.
