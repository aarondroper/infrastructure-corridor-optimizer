# SVTM Bulk Package and Persistent DEM Recovery

## Objective

Evaluate and, if valid, use the official Data.NSW/SEED SVTM Extant C2.0.M2.2
download package as a bulk delivery of the approved vegetation dataset, while
restoring the approved Copernicus GLO-30 DEM to persistent storage.

## Context

The approved SVTM REST service is unstable during S1 capture. Data.NSW publishes
an Extant Download Package with the same C2.0.M2.2 release identifier. The existing
REST page cache is retained for comparison and fallback; it must not be hammered.

## Approach

- verify official package identity, release, licence, URL, and declared format from
  Data.NSW/SEED metadata and official technical notes;
- implement persistent, resumable, byte-bounded package acquisition with safe ZIP
  member inspection and no implicit statewide extraction;
- validate package geometry, CRS, required PCT/vegetation attributes, S1 coverage,
  and reconciliation against known REST inventory evidence before publication;
- restore and validate four persistent Copernicus GLO-30 S1 tiles;
- preserve all raw bulk artifacts outside Git and record acquisition manifests.

## Acceptance criteria

- package identity is demonstrably the approved extant C2.0.M2.2 dataset;
- package download and extraction cannot expand into system temporary storage or
  exceed configured archive/materialization/working-set limits;
- incomplete, invalid, statewide-only, or attribute-incompatible package content is
  rejected rather than silently used;
- DEM manifest and all tiles validate in persistent storage;
- no full grid or route is generated until SVTM package completeness is verified.

## Risks

- SEED bulk delivery may be protected by a web challenge or its package may be too
  large for the current access path;
- package internals may use an ESRI format requiring a GIS reader not installed in
  the dependency-light environment;
- package content may differ from the REST release despite similar naming, which is
  an owner decision boundary rather than an implementation assumption.
