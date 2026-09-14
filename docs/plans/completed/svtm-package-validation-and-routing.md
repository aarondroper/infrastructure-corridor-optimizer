# Validate Manual SVTM Package and Derive S1 Routes

## Objective

Safely validate the owner-supplied official SVTM Extant C2.0.M2.2 ZIP, derive a
persistent S1 analytical representation without statewide extraction, and continue
through geographic grid construction and real offline route generation if the source
and all required constraint layers support it.

## Context

The SEED endpoint blocked programmatic access, but the owner downloaded the official
ZIP locally. Central-directory inspection shows both a Quickview ESRI geodatabase
and a classified 5 m GeoTIFF/VAT representation, plus MXD symbology. The archive is
larger than the package download cap and its declared full extraction is larger than
the extraction cap, so the workflow must preserve the safety limits through explicit
local inspection and selective S1 materialization.

## Approach

- record archive size, SHA-256, member inventory, official metadata evidence, and
  whole-archive CRC status;
- inspect the geodatabase and raster metadata using bounded local tooling without
  extracting the statewide geodatabase;
- selectively materialize only the representation required for S1, under persistent
  ignored storage and the archive-plus-selected-output working-set bound;
- validate S1 coverage, CRS, geometry/raster integrity, attributes/classes,
  duplicate/nodata behavior, and provenance;
- reconcile vector feature counts/IDs with REST evidence when the geodatabase can be
  read; treat raster equivalence through its value attribute table and coverage when
  it is the cleaner grid input;
- derive aligned geographic cost grids from the validated DEM and source layers,
  generate the approved offline routes, independently assess them, and update state;
- stop for owner review if representation choice changes the approved analytical
  interpretation or if an approved source cannot support a defensible S1 result.

## Acceptance criteria

- no statewide extraction or unbounded temporary materialization occurs;
- the package is proven readable and its provenance is recorded outside Git;
- at least one analytical SVTM representation passes S1/CRS/content validation;
- grid inputs and outputs carry source/configuration provenance and fail closed on
  incomplete coverage;
- three deterministic approved-preset routes are generated from real geographic
  grids, with route assessment metrics and no unsupported completion claim;
- tests and quality gates pass, documentation matches reality, and this plan plus
  the preceding recovery plan are archived only when the applicable frontier is
  genuinely complete.

## Risks

- the geodatabase may require an unavailable or incompatible GIS reader;
- the 5 m statewide raster is too large for direct S1 processing without a bounded
  window/read path and deliberate resampling;
- remaining source layers may not all have complete persistent artifacts;
- choosing raster versus vector for the vegetation penalty may require owner review
  if their analytical meanings differ materially.

## SVTM package outcome — 14 September 2026

The owner-supplied archive is a valid 4,720,800,490-byte ZIP with SHA-256
`e8d92c9a2b661b4265df90e239608a7a6e7c17bde0d57809a08f67182b187952`, 72 members,
and valid CRCs. It contains the official C2.0.M2.2 classified 5 m GeoTIFF/VAT,
Quickview geodatabase, and MXD symbology. The raster was read directly through
GDAL `/vsizip/`; its EPSG:3308, 5 m, uint16, nodata-65535 metadata and VAT were
validated, and a 789x1005 100 m S1 raster was published under ignored persistent
storage. The declared full extracted size is 16.1 GB, so the 12.6 GB geodatabase
was not extracted and the package's 8 GB extraction safety limit remains intact.
The raster is accepted as the same approved native-vegetation dataset and no
methodological substitution was made. Exact REST feature-count reconciliation is
not applicable to the classified raster representation.

The downstream geographic work also completed: the validated source stack produced
a 990x767 EPSG:7856 100 m S1 bundle and three real A* route assets with GeoJSON
assessment outputs. The remaining work is application packaging and finer
feature-level assessment, so this recovery plan is complete.
