# Acquisition Operations and Storage Safety

This document records the storage contract for potentially large source captures.
Raw source data is external build input and is ignored by Git; it must not be
stored in `/tmp` for a full run.

## Current storage paths

The production vector CLI defaults to these paths, resolved relative to the
repository working directory:

- `data/external/vectors/` — final staged-and-published ArcGIS feature artifacts and
  the compact `acquisition_manifest.json`;
- `data/cache/arcgis/` — resumable page caches, under fixed
  `<source-id>--<component>--page-<page-size>/tile-####-page-#####.json`
  namespaces; the page size is part of the namespace so incompatible page
  batches cannot be resumed accidentally;
- `data/external/dem/copernicus-glo30-s1/` — Copernicus GeoTIFF/XML tiles and
  `dem_manifest.json`.
- `data/cache/seed/svtm-c2.0.m2.2/` — the official SVTM package archive, its
  `.zip.part` resumable download, and its `.state.json` acquisition state;
- `data/external/vectors/svtm-package/` — the package inspection manifest and any
  explicitly selected members after a geospatial reader validates them. The CLI
  never extracts the statewide package implicitly.

The vector writer creates `data/external/vectors/.staging-<random>/` beneath the
selected output directory. It moves completed artifacts into the output directory
only after all selected pages validate. `write_manifest` creates a sibling
`<manifest>.tmp` file and atomically replaces the destination. The DEM downloader
creates a sibling hidden temporary file beside each destination tile, replaces the
tile after checksum validation, and removes the temporary file in its normal
failure path.

Other acquisition/report commands write only their explicitly supplied manifest
or report path (the small-command defaults are `data/source_manifest.json`,
`data/source_probe.json`, and `data/terrain_selection.json`). There is no hidden
retry database, daemon queue, or automatic global cache. ArcGIS retry state exists
only in process memory; vector resume state is the validated page JSON under the
selected cache root; DEM resume state is the already checksum-verified tile files
under the selected DEM output. Unit tests use Python temporary directories, but
that is test scaffolding rather than a production acquisition location.

No production code hard-codes `/tmp` for source data. The only uses of Python's
temporary-file APIs are the vector staging directory (explicitly created beneath
the selected output root) and the DEM per-tile download temporary file (explicitly
created beside the selected tile). If a caller supplied `/tmp` as either root in
the old CLI, those descendants therefore landed in `/tmp`; the new production CLI
rejects that unless the bounded-probe override is explicit.

The CLI rejects output/cache paths under Python's `tempfile.gettempdir()`,
`/var/tmp`, or `/dev/shm` unless `--allow-temporary-path` is explicitly supplied
for a small bounded probe. The library API accepts caller-selected paths for test
fixtures; production commands should use the persistent defaults or explicit
project data paths. Output and cache roots must be separate.

The package downloader uses only the persistent cache path for the archive and
resume state. Selected-member extraction creates a short-lived `.staging-svtm-*`
directory beside the persistent package output, then atomically moves the selected
member tree into place. It does not use Python's default temporary directory for
large package data.

## Safety limits

The configured ArcGIS limits are:

| Limit | Value | Purpose |
| --- | ---: | --- |
| response and page bytes | 32 MB | reject unexpectedly large service responses before page serialization grows further |
| unique expected features | 300,000 | stop before feature retrieval if source scale changes materially |
| tiled inventory IDs | 1,000,000 | bound overlap amplification across tiles |
| expected pages | 1,000 | bound pagination work before downloads |
| cache bytes | 8 GB | bound all retained page caches under the selected cache root |
| staging bytes | 4 GB | bound the in-progress published artifact |
| combined cache + staging bytes | 12 GB | bound the main duplicate working set |

The SVTM bulk-package limits are:

| Limit | Value | Purpose |
| --- | ---: | --- |
| archive bytes | 4 GB | refuse an unbounded or unexpectedly large package download |
| declared extracted member bytes | 8 GB | reject ZIP bombs or statewide materialization beyond the configured bound |
| archive plus selected extraction | 12 GB | keep an explicit package archive and selected analytical members within the working-set budget |
| ZIP members | 100,000 | reject pathological package inventories before inspection |

The acquisition query records feature-payload bytes, newly written cache-page
bytes, cache-page count, tile inventory, expected pages, and returned counts. Each
page is checked against the page limit; the cache and combined staging working set
are checked as pages complete. A limit failure removes the incomplete staging
artifact and publishes no acquisition manifest. Validated page caches remain for
an explicit `--resume` rerun.

The package downloader records archive bytes, SHA-256, response state, and resume
offsets. It requires a positive `Content-Length`, refuses to append unless a resumed
response is HTTP 206 with a matching `Content-Range`, and rejects non-ZIP responses
such as the current SEED HTTP 202 web challenge. A package is not analytically
accepted from ZIP structure alone: a reader-produced content report must show
complete S1-scoped coverage, polygon geometry, EPSG:3308, required PCT/vegetation
fields, zero duplicate IDs, and reconciliation to the known REST count of 216,808
features.

## Audit findings (13 September 2026)

The original incident cannot be attributed definitively because the temporary
directories were deleted before forensic inspection. Repository evidence does
show that a full run can be multi-gigabyte:

- the current bounded count-only probes returned 216,808 SVTM polygons and 68,320
  Hydroline features in S1;
- a 20-feature geometry sample serialized at about 8.1 KB per SVTM feature and
  0.77 KB per Hydroline feature;
- this implies roughly 1.7–2.0 GB for a compact SVTM feature artifact and about
  53 MB for Hydroline, before cache/staging duplication and tile-boundary overlap;
- the 0.1° SVTM configuration creates up to 81 tiles. A polygon intersecting more
  than one tile is cached in each tile page, then deduplicated in the published
  artifact. That intentional resumability duplication can materially increase
  cache size;
- a fresh cache directory or namespace is not automatically removed after a
  failure. Repeated runs under fresh temporary paths can therefore retain several
  complete partial caches. A single estimated run does not explain 396 GB, but
  repeated abandoned runs, extreme overlap, or another process could plausibly
  account for that scale.

Retries do not create new page filenames: they repeat the same HTTP request and
replace the same cache page only after validation. A failed run removes its staged
artifact in normal exception handling but intentionally retains validated pages for
resume; an abrupt process kill can leave a `.staging-*` directory or a sibling
`.tmp` file, which is why the cleanup procedure is dry-run-first. A new cache root
or namespace, however, is a new physical copy by design and must be cleaned up
explicitly.

The DEM workflow is much smaller for S1: four public GLO-30 tiles totaling about
163 MB from the observed object sizes, plus XML metadata, one temporary tile copy
while downloading, and a small manifest. It does not create a page-cache namespace.
The DEM CLI bounds the tile set to 16 tiles and downloaded GeoTIFF bytes to 300 MB
by default; S1's four-tile set is below both limits.

The persistent Copernicus artifact was restored on 13 September 2026. Its four
tiles and XML sidecars occupy 160,523,100 bytes (`du -sb`), and its manifest
records complete S1 coverage, EPSG:4326, nominal 30 m/one-arcsecond resolution,
and XML nodata `-32767`.

## Official SVTM bulk-package investigation

Data.NSW metadata identifies the resource as the NSW State Vegetation Type Map -
SVTM (Extant), release C2.0.M2.2 (December 2025), under Creative Commons
Attribution. The configured SEED resource is an acquisition-engineering delivery
alternative for that same approved dataset, not a vegetation-source substitution.
The Data.NSW API does not publish a package byte size. The resource page describes
the supplied download package as an ArcGIS 10.8 MXD and/or layer file for suggested
symbology, while the analytical map data is separately described as an ESRI Feature
Class and 5 m GeoTIFF. Therefore a downloaded ZIP is not assumed to contain vector
data: the inspector rejects a documentation-only package, and a geospatial reader
must supply the content report before model use.

A bounded live probe on 13 September 2026 received HTTP 202 with an interactive
web challenge and wrote only the persistent 423-byte state file. No archive bytes
were written and no retry loop was started. Do not repeatedly hammer this endpoint.
When access is available, use:

```bash
PYTHONPATH=src python3 scripts/acquire_svtm_package.py \
  --cache-dir data/cache/seed/svtm-c2.0.m2.2 \
  --output-dir data/external/vectors/svtm-package \
  --timeout 60 --max-retries 3 \
  --content-report <reader-produced-s1-content-report.json> \
  --extract-member <explicit-vector-member> \
  --extract-member <matching-attribute-sidecar>
```

First inspect the ZIP manifest/member list and select only the vector and required
sidecars. The content report must be generated from those selected members and must
reconcile the REST inventory/count evidence before the artifact is accepted.

The acquisition logic only discovers IDs using tiles generated from the configured
S1 envelope. Feature pages are requested by those exact IDs, without re-sending an
unbounded geometry filter. Full source geometries may extend beyond the envelope
because ArcGIS returns whole intersecting features; that is expected source
semantics, not an unbounded query. Tile overlap is deduplicated by object ID with a
small coordinate tolerance for reprojection round-off, while genuine conflicting
duplicates fail validation.

## Cleanup and safe resumption

Review abandoned directories without deleting anything:

```bash
PYTHONPATH=src python3 scripts/cleanup_acquisition_storage.py \
  --cache-dir data/cache/arcgis \
  --output-root data/external/vectors \
  --older-than-hours 24
```

After confirming that no acquisition process is running, repeat with `--delete`.
The cleanup script only targets cache namespace directories and `.staging-*`
directories older than the threshold; it does not remove final artifacts or
manifests. For a failed DEM run, inspect `data/external/dem/.../tiles/` and rerun
the DEM command: valid existing tiles are checksum-reused and no manifest is
published until every tile validates.

Future full captures should be run one component at a time from persistent roots,
with the same cache root retained for resume. SVTM uses a measured 250-feature
page size because a 1,000-feature request exceeded the unchanged 32 MB response
ceiling; the largest observed 250-feature page was 28.1 MB. The safe vector
workflow is:

```bash
PYTHONPATH=src python3 scripts/acquire_vector_sources.py \
  --source-id nsw-hydrography --component hydrography_line \
  --output-dir data/external/vectors/s1-hydrography-line \
  --cache-dir data/cache/arcgis/s1 \
  --timeout 30
```

If interrupted after validated pages are cached, rerun the identical command with
`--resume`. Do not create a new cache directory unless intentionally starting a
new source snapshot, and clean the old namespace afterward. To remove one known
abandoned namespace without scanning or touching sibling captures, use the
explicit `--cache-namespace <path>` cleanup option; review its dry-run output
before adding `--delete`. The current SVTM run has 190 validated cached pages but
no published artifact because the service subsequently returned repeated HTTP 500
and timeout/HTTP 400 failures during tiled inventory. It is resumable with:

```bash
PYTHONPATH=src python3 scripts/acquire_vector_sources.py \
  --source-id nsw-svtm --component native_vegetation \
  --output-dir data/external/vectors/s1-native-vegetation-final \
  --cache-dir data/cache/arcgis/s1 --timeout 30 --resume
```
