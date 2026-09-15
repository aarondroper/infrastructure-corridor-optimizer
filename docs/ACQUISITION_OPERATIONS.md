# Acquisition operations

Large source captures are reproducible build inputs, not runtime application
assets. They stay outside Git under persistent project storage and are never
placed in the system temporary directory for a full run.

## Persistent storage contract

The production acquisition commands resolve their defaults relative to the
repository:

- `data/external/vectors/` — validated final vector artifacts and compact
  acquisition manifests;
- `data/cache/arcgis/` — resumable ArcGIS page caches, namespaced by source,
  component, and page size;
- `data/cache/seed/svtm-c2.0.m2.2/` — the official SVTM package, resumable
  `.zip.part` state, and package acquisition metadata;
- `data/external/vectors/svtm-package/` — the selected S1 SVTM raster and
  validation reports;
- `data/external/dem/copernicus-glo30-s1/` — four validated GLO-30 tiles,
  XML sidecars, and `dem_manifest.json`.

Vector staging directories are created beneath the selected output root and are
atomically finalized. Manifest writes use sibling temporary files. DEM downloads
use a temporary file beside the destination tile and replace it only after
checksum validation. The SVTM reader uses GDAL `/vsizip/` and does not extract
the statewide geodatabase implicitly.

Production commands reject roots under Python's temporary directory, `/var/tmp`,
or `/dev/shm`; the explicit `--allow-temporary-path` option exists only for
small bounded probes and test fixtures. No production command has an implicit
global cache or retry database. Validated pages are retained for `--resume`, so
abandoned cache namespaces must be reviewed and removed with the cleanup command
below.

## Guardrails and resumability

The ArcGIS acquisition limits are configured in the source code and summarized
here:

| Limit | Default | Purpose |
| --- | ---: | --- |
| response/page bytes | 32 MB | reject unexpectedly large responses |
| expected unique features | 300,000 | detect material source-scale changes |
| tiled inventory IDs | 1,000,000 | bound overlap amplification |
| expected pages | 1,000 | bound pagination |
| retained cache bytes | 8 GB | bound page-cache growth |
| staged artifact bytes | 4 GB | bound in-progress output |
| cache plus staging | 12 GB | bound duplicate working set |

The SVTM package limits are a 4 GB archive, 8 GB declared extracted members,
12 GB archive plus selected extraction, and 100,000 ZIP members. The owner-
supplied archive is 4,720,800,490 bytes, so it is recorded as an exception to
the normal download cap rather than downloaded by the CLI. The validator records
that exception while still bounding selected extraction and working set. Limits
are not weakened for a normal source run.

Each request validates HTTP status, content type, payload bytes, page identity,
feature count, and study-envelope relationship before caching. Tiled inventories
are reconciled and overlapping features are deduplicated before finalization.
Retries use bounded backoff and replace the same validated page name; they do not
create a new copy. A failed run publishes no final manifest. A process killed
mid-write may leave a staging directory or `.tmp` file, which is why cleanup is
explicit and dry-run-first.

Before a full capture, the CLI reports the cache, output, staging, limits, and
estimated working set. It fails safely on runaway response, page, feature, cache,
staging, or combined-working-set growth. The configured study envelope is passed
to every inventory and query; pages whose geometries fall outside the allowed
relationship are rejected rather than silently accepted.

## Current S1 captures

The validated S1 inventories contain:

| Component | Features | Representation |
| --- | ---: | --- |
| NPWS protected land | 20 | vector |
| Hydroline | 68,320 | vector |
| Hydroarea | 12,652 | vector |
| roads | 46,092 | vector |
| railways | 415 | vector |
| SVTM REST inventory evidence | 216,808 | polygon inventory; not the raster acceptance gate |

The approved SVTM C2.0.M2.2 package contains the analytical classified 5 m
GeoTIFF, its value-attribute table and metadata, an MXD, and a large Quickview
geodatabase. The archive is a valid 72-member ZIP with SHA-256
`e8d92c9a2b661b4265df90e239608a7a6e7c17bde0d57809a08f67182b187952`. Its
statewide geodatabase declares approximately 12.6 GB and the package declares
approximately 16.1 GB of extracted members, so only the S1 raster is read through
`/vsizip/` and materialized. The S1 raster is EPSG:3308, uint16, nodata 65535,
with 1,687 VAT records. Its manifest and content report are written under the
ignored SVTM package directory.

The four GLO-30 tiles occupy 160,523,100 bytes including XML sidecars. They
cover S1, use EPSG:4326 source coordinates and nominal one-arcsecond/30 m
resolution, and record XML nodata `-32767`; the grid stage reprojects them to
EPSG:7856.

## Reproducible workflow

Install the optional geospatial dependencies, then use the source-specific
commands with the persistent defaults:

```bash
python3 -m pip install -e '.[geospatial]'
PYTHONPATH=src python3 scripts/acquire_vector_sources.py --help
PYTHONPATH=src python3 scripts/acquire_copernicus_dem.py --help
PYTHONPATH=src python3 scripts/validate_svtm_raster.py \
  --archive data/cache/seed/svtm-c2.0.m2.2/svtm_nsw_extant_pct_vc2_0_m2_2_108.zip \
  --output-dir data/external/vectors/svtm-package --cell-size-m 100
```

After all required manifests validate, the grid, route, assessment, and web
asset commands are shown in [ARCHITECTURE.md](ARCHITECTURE.md) and use only
project-relative persistent paths. Source identities, versions, licenses, and
links are catalogued in [DATA_SOURCES.md](DATA_SOURCES.md).

## Cleanup

Review abandoned cache pages, stale staging directories, and old package state
with:

```bash
PYTHONPATH=src python3 scripts/cleanup_acquisition_storage.py \
  --cache-dir data/cache/arcgis \
  --output-root data/external/vectors \
  --older-than-hours 24
```

After reviewing the exact candidates, add `--delete` to remove only the reported
stale acquisition artifacts. Keep the current manifests and validated source
artifacts unless deliberately rebuilding them.

## Operational boundary

Acquisition is an offline build concern. The public application receives only
the compact generated route/assessment asset; it never downloads or stores raw
GIS sources in the browser.
