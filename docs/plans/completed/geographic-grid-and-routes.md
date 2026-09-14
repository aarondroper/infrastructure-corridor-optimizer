# Derive the S1 Geographic Grid and Offline Routes

## Objective

Transform the validated S1 source artifacts into one provenance-rich 100 m
EPSG:7856 normalized cost-grid bundle, then generate the approved shortest,
balanced, and environmental offline route assets.

## Context

The approved source stack is now available in persistent ignored storage:
Copernicus GLO-30 DEM tiles, SVTM's C2.0.M2.2 classified raster window,
NPWS estate, roads, railways, hydrography-line, and hydrography-area. The
existing routing core accepts rectangular normalized arrays but there is no
geographic derivation implementation.

## Approach

- validate each source manifest and artifact before processing;
- use the configured S1 envelope transformed to EPSG:7856 and a 100 m north-up
  analysis grid, with explicit coverage checks and deterministic dimensions;
- reproject DEM tiles and derive a clamped slope surface;
- rasterize polygon/line indicators from validated ArcGIS JSON, preserving
  source feature counts and provenance;
- reproject the bounded SVTM classified raster into the common grid using nearest
  resampling and treat its nodata as unavailable input;
- map each source to the approved provisional seven-component penalty model and
  write a compact JSON grid bundle with source checksums/manifests;
- run the existing precomputed-route generator and add independent route-grid
  validation/metrics where supported.

## Acceptance criteria

- no source outside the configured S1 envelope is used to derive the grid;
- the grid is rectangular, aligned, finite where source coverage is valid, and
  carries EPSG:7856, cell size, endpoint cells, source provenance, and nodata
  diagnostics;
- every configured component is represented and the cost model remains the
  approved penalty-based sensitivity model;
- all three approved presets generate deterministic route assets from the real
  geographic bundle;
- tests cover reprojection/rasterization guards and failure on missing or
  incomplete inputs;
- quality gates and documentation reflect measured output sizes and limitations.

## Risks

- public ArcGIS JSON artifacts are large and should be streamed or parsed with
  bounded memory where practical;
- Copernicus GLO-30 has a coarse 30 m nominal resolution relative to the 100 m
  MVP grid and its surface is not a construction-grade terrain model;
- indicator rasterization and penalty mappings are provisional analytical
  assumptions and must remain documented as such;
- a JSON representation of a roughly 800x1,000 grid may be large but remains
  within the persistent storage budget.

## Outcome — 14 September 2026

The complete persistent source stack passed independent artifact validation. The
derived bundle is 990x767 cells at 100 m in EPSG:7856, with 8,329 DEM/SVTM nodata
cells excluded and both endpoint cells valid. All seven approved components are
present and carry source manifest/checksum provenance. The approved A* generator
produced shortest, balanced, and environmental routes of 732, 741, and 786 cells;
the assessment stage published EPSG:7844 GeoJSON and lengths of 95.76 km, 96.28 km,
and 99.17 km. Standard tests pass (82, one optional geospatial skip) and the full
temporary GIS environment passes all 82 tests. Feature-level crossing inventories,
frontend assets, and production-quality calibration remain outside this plan.
