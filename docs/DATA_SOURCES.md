# Data sources and provenance

The Infrastructure Corridor Optimizer uses public source data for a contained S1
screening study between fixed Bayswater and Eraring-area endpoints. Acquisition is
validated before data enters the analytical pipeline, and large source artifacts are
kept outside Git. The source snapshot recorded in `config/model.json` is 13 September
2026.

## Sources used by the S1 model

| Source | Provider and link | Role | Format / source CRS | Important notes |
| --- | --- | --- | --- | --- |
| Electricity Infrastructure | [Geoscience Australia dataset](https://pid.geoscience.gov.au/dataset/ga/151179), [ArcGIS service](https://services.ga.gov.au/gis/rest/services/Electricity_Infrastructure/MapServer) | Fixed Bayswater and Eraring endpoints | ArcGIS REST; GDA2020 / EPSG:7844 | The captured records are Bayswater object ID 251 and Eraring object ID 286. |
| NPWS Estate | [NSW dataset](https://data.nsw.gov.au/data/dataset/nsw-national-parks-and-wildlife-service-npws-estate3f9e7), [REST layer](https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/EDP/Estate/MapServer/0) | Protected or managed land indicator | ArcGIS REST; source EPSG:4283, processed in EPSG:7856 | CC BY is documented for the source. It is a weighted indicator, not a universal legal exclusion. |
| State Vegetation Type Map (Extant) | [NSW dataset](https://data.nsw.gov.au/data/dataset/nsw-state-vegetation-type-map), [SVTM service](https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/VIS/SVTM_NSW_Extant_PCT/MapServer/3), [official package resource](https://data.nsw.gov.au/data/dataset/nsw-state-vegetation-type-map/resource/38cb096e-25e4-42e1-9996-807765ec7c47) | Native-vegetation sensitivity indicator | Official C2.0.M2.2 classified 5 m GeoTIFF/VAT; source EPSG:3308, windowed and aligned to EPSG:7856 | December 2025 release; Creative Commons Attribution. The raster representation supplies PCT and vegetation attributes for the model. |
| NSW Hydrography | [NSW dataset](https://data.nsw.gov.au/data/en/dataset/nsw-hydrography), [ArcGIS service](https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Hydrography/MapServer) | Hydroline and hydro-area crossing penalties and assessment | ArcGIS REST; source EPSG:3857, processed in EPSG:7856 | Hydroline, named-watercourse, and hydro-area layers are queried through bounded object-ID paging. |
| NSW Transport Theme | [FeatureServer](https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Transport_Theme_multiCRS/FeatureServer), [roads](https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Transport_Theme_multiCRS/FeatureServer/5), [railways](https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Transport_Theme_multiCRS/FeatureServer/7) | Road and railway crossing penalties and assessment | ArcGIS REST; source EPSG:7844, processed in EPSG:7856 | Road and railway intersections are not universal exclusions. Source attributes are retained in external artifacts and compact assessment outputs. |
| Copernicus DEM GLO-30 | [Copernicus Data Space collection](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM), [AWS distribution](https://registry.opendata.aws/copernicus-dem/) | Terrain elevation and derived slope | Public one-arcsecond / nominal 30 m GeoTIFF tiles; EPSG:4326, processed in EPSG:7856 | The validated four-tile S1 fallback was used because the preferred ELVIS/NSW raster was not available in the execution environment. XML nodata is `-32767`. |

OpenStreetMap contributors provide the contextual basemap in the web application.
The basemap is not an analytical input; attribution is retained in the map.

## Endpoint and study configuration

The processing envelope is GDA2020 longitude/latitude bounds 150.82–151.62 E and
32.27–33.15 S. The analytical grid is 100 m in EPSG:7856. Endpoint coordinates,
source object IDs, source dates, component roles, and preset weights are versioned in
`config/model.json`.

## Published S1 evidence

Validated external captures contain 20 NPWS features, 46,092 road features, 415
railway features, 68,320 hydrography-line features, and 12,652 hydrography-area
features. The official SVTM package is a 4,720,800,490-byte C2.0.M2.2 ZIP with a
classified raster and VAT; its 5 m raster was read directly from the archive and
materialized only for the S1 window. The known REST SVTM inventory of 216,808
polygons is retained as validation evidence, but is not used as a feature-count gate
for the raster representation.

The compact web asset contains derived route geometries, metrics, inventories, and
provenance-oriented metadata. Raw geometries, source archives, caches, and DEM tiles
remain outside Git.

## Interpretation and licensing

Source licences and attribution requirements should be checked again when acquiring
new snapshots. Public source availability does not establish land access, legal
feasibility, environmental approval, or construction suitability. The model treats
environmental and crossing layers as weighted screening indicators, as described in
[the analytical model](ANALYTICAL_MODEL.md).
