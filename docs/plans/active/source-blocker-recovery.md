# Recover Source Acquisition for Geographic Derivation

## Objective

Make the approved SVTM and NSW Hydrography inputs reproducibly capturable at S1
scale, with spatial chunking, retries, external page caching, resumability,
manifest-level completeness checks, and bounded persistent storage. Investigate
approved DEM access in parallel, but do not substitute a source without owner review.

## Context

The existing ArcGIS adapter queries one envelope and pages object IDs. This is
insufficient for the approximately 216,808-feature SVTM layer and previously
stalled hydrography-line capture. The approved SVTM feature layer is queryable, but
live batched requests have returned intermittent ArcGIS 500 errors. No DEM artifact
is present in the repository; the approved terrain order is ELVIS/NSW first and
Copernicus GLO-30 second.

## Approach

- split bounded ArcGIS object-ID discovery into explicit envelope tiles;
- fetch each tile’s IDs in pages without repeating the spatial filter on feature
  requests, validate exact returned IDs/CRS/geometries, and deduplicate boundary
  overlaps;
- add retry/backoff to transient ArcGIS/network failures;
- cache complete pages outside the final output and allow a rerun to resume from
  validated cache entries;
- publish only after all expected tile IDs have corresponding valid features;
- add deterministic failure/retry/cache tests and update source provenance docs;
- inspect approved DEM access and continue only if a complete reproducible artifact
  can be acquired without unavailable credentials.
- audit temporary-storage behavior after the reported disk-usage incident, add
  response/page/inventory/storage limits, persistent-path defaults, and cleanup tooling;
- pause full live captures until the owner has reviewed the audit and safe resume
  workflow.

## Acceptance criteria

- tile and page metadata make expected versus returned coverage explicit;
- partial or stale cached pages cannot be accepted silently;
- transient failures are retried, permanent failures leave no published manifest,
  and a later run can reuse validated completed pages;
- current sources retain their existing behavior and tests;
- live source topology/count evidence and DEM findings are documented accurately.

## Risks and limits

This work does not change the approved source set, penalty model, or study envelope.
The full SVTM/hydrography captures may still be blocked by service availability or
volume. Geographic grid derivation remains gated on complete vector artifacts and an
approved DEM artifact. Large live materialization is not restarted during this audit.

## Audit outcome — 13 September 2026

The original temporary files were deleted, so attribution of the approximately
396 GB `/tmp` growth is not definitive. The implementation could plausibly create
multi-gigabyte working sets because an in-progress vector artifact and resumable
page cache both contain serialized geometry, and each new cache root remains after
a failed run. The 0.1° SVTM tiling can also repeat boundary-intersecting features
across pages before publication deduplicates them. Repository evidence does not
support attributing hundreds of gigabytes to one normal S1 run; repeated abandoned
temporary runs, unusually high overlap, or another process remain possible.

Implemented safeguards are documented in `docs/ACQUISITION_OPERATIONS.md`: default
persistent paths, temporary-path refusal in production CLIs, explicit path reporting,
pre-download inventory limits, response/page/storage limits, byte counters in query
metadata, separate output/cache roots, page-size-specific cache namespaces, and
dry-run-first abandoned-directory cleanup with exact namespace targeting.

Hydroline was subsequently acquired and independently validated on 13 September
2026: 68,320 unique features, 355 pages across 16 tiles, 965 tiled inventory
overlaps reconciled, 105.2 MB final bundle, and 108.6 MB persistent cache. SVTM
was restarted with an evidence-based 250-feature page size after a 1,000-feature
request exceeded the 32 MB response ceiling. It reached 190 validated pages and
approximately 1.16 GB of page cache / 333.5 MB staged output before a repeated
ArcGIS 500 and later bounded probes returned HTTP 400/timeouts. No SVTM artifact
was published; the page-250 cache is retained for resumable continuation. Full
SVTM capture and geographic derivation remain blocked by current source-service
reliability, not by observed storage pressure.
