# Materialize Large Approved Vector Layers

## Objective

Use the verified staged ArcGIS acquisition path to capture the remaining large
hydrography and road layers for the S1 processing envelope into external temporary
build directories.

## Implemented and investigated

- Added live sparse-topology fallback for ArcGIS services whose root layer listing
  omits child `type` and `geometryType` fields; layer detail metadata is now fetched
  before queryability and geometry validation.
- Confirmed the road service accepts at most 150 IDs per feature request in this
  envelope. Added a layer-level `page_size` override while retaining the global 200
  default used by the other configured layers.
- Added regression coverage for sparse hydrography metadata and source-specific page
  size selection.
- Attempted hydrography and roads in external `/tmp` directories only.

## Outcome

- Roads succeeded: 46,092 object IDs and 46,092 feature records were written in 308
  complete pages, with a valid EPSG:7856 artifact and compact manifest. The raw road
  artifact is 34.4 MB and remains outside Git.
- Hydrography passed topology resolution and began streaming, but the public service
  stalled during a later feature-page request. The run was interrupted after staged
  output had begun; cleanup removed the staging directory and published no manifest.
- Standard-library tests: 37 passed. JSON parsing and whitespace checks passed.

## Limits and follow-up

The hydrography source remains an external availability/performance limitation, not a
reason to weaken validation. A future retry may use a smaller page size or a bounded
component/layer strategy if evidence supports it. Successful road and prior NPWS/
railway captures are staging inputs, not derived cost surfaces; DEM/SVTM acquisition,
normalization, rasterization, route generation, and assessment remain future work.
