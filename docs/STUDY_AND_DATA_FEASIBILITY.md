# Study and Data Feasibility

**Research status:** Evidence assembled for owner review

**Research date:** 13 September 2026

**Decision status:** Owner selections recorded: S1, existing public Bayswater/Eraring
endpoint records, penalties for environmental/crossing factors, the approved
sensitivity presets, offline precomputed routes, and ELVIS/NSW DEM as primary terrain
source with Copernicus DEM GLO-30 as explicit fallback.

## Conclusion

The preferred Hunter / New England direction is feasible for a compact preliminary
corridor-screening case study. The strongest candidate is a Hunter transmission
context between the Bayswater area in the Upper Hunter and the Lake Macquarie / Olney
area. EnergyCo publicly describes a Hunter Transmission Project corridor connecting
the Bayswater and Eraring areas and publishes a current project map; the project page
also identifies environmental and land-use trade-offs that would make the routing
comparison meaningful. The published corridor is context only and must not be treated
as the optimizer's answer.

The source stack is viable, but the pipeline should use current GDA2020 or multi-CRS
services, spatially filtered requests, and pinned acquisition metadata. The NSW
Biodiversity Values Map should not be a core static cost surface without a dated
snapshot because the agency says its data is updated regularly and valid only on the
day of download.

## Candidate study scenarios

| ID | Candidate context | Why it is useful | Main risk / unresolved choice |
| --- | --- | --- | --- |
| S1 | **Upper Hunter to Lake Macquarie:** Bayswater Power Station to the selected Eraring public asset, with the proposed Olney switching-station location shown as contextual reference | Best demonstration of a non-trivial corridor crossing mining/industrial land, woodland/protected areas, waterways, roads, and rail; directly related to a current public transmission-planning context | The current project alignment is evolving, so it must remain a comparison context rather than a target route. |
| S2 | **Hunter-Central Coast REZ:** a Kurri Kurri-area connection to the Muswellbrook-area network | More compact and closely aligned with EnergyCo's described Hunter-Central Coast network infrastructure work, including upgrades between Kurri Kurri and Muswellbrook | Much of the public project is an upgrade of existing distribution infrastructure rather than a new unconstrained corridor; may produce weaker route differentiation. |
| S3 | **Upper Hunter local connection:** Bayswater-area asset to a Muswellbrook-area substation | Smallest build and easiest debugging/benchmarking case; suitable as a technical feasibility slice | Lower landscape diversity and potentially too little route-choice separation for the portfolio story. |

### Recommendation

Carry S1 into the owner decision with a compact envelope around the Bayswater–Singleton–
Broke–Cessnock–Olney/Eraring context. Prefer existing, queryable public energy assets
as the two fixed endpoints for reproducibility; use any proposed switching-station
location only if the owner explicitly accepts a planning-stage endpoint. Keep the
EnergyCo published corridor visible as a reference layer only, with clear labeling
that it is not the generated recommendation.

**Owner selection:** Carry S1 forward using the existing public Bayswater and Eraring
records as the fixed endpoints. The live Geoscience Australia query resolved
Bayswater object ID 251 and the 2,880 MW Eraring object ID 286; the exact identifiers
and coordinates are captured in `config/model.json`. The proposed Olney location
remains contextual reference only.

**Owner selection:** Treat environmental and crossing factors as weighted penalties
and assessment metrics rather than universal hard exclusions. This does not remove
the need to treat missing or invalid source coverage as unavailable during processing,
and it does not establish legal feasibility.

## Candidate source matrix

| Role | Candidate source and access | Evidence / technical fit | Feasibility assessment |
| --- | --- | --- | --- |
| Energy endpoints and existing network context | [Geoscience Australia Electricity Infrastructure](https://pid.geoscience.gov.au/dataset/ga/151179), [MapServer](https://services.ga.gov.au/gis/rest/services/Electricity_Infrastructure/MapServer), and [WFS](https://services.ga.gov.au/gis/services/Electricity_Infrastructure/MapServer/WFSServer) | Current service exposes substations, major power stations, and power lines in GDA2020 (EPSG:7844). The live schema includes feature name, status, voltage, locality, state, source dates, confidence, latitude, and longitude. | **Recommended.** Public, machine-readable, nationwide, and suitable for reproducible candidate discovery. Record the 2026 service version and source dates. The live service returned HTTP 200 for metadata and WFS capabilities when queried with a normal client user-agent; filtered feature queries still need to be implemented and tested in the pipeline. |
| Study context | [EnergyCo Hunter-Central Coast REZ project](https://www.energyco.nsw.gov.au/our-projects/hunter-central-coast-rez/network-infrastructure-project) and [Hunter Transmission Project corridor-selection page](https://energyco.nsw.gov.au/our-projects/hunter-transmission-project/corridor-selection) | EnergyCo provides a public Hunter context, a GIS boundary download for the HCC REZ, and a current description of the Hunter Transmission Project corridor and its planning trade-offs. | **Recommended as context only.** Useful for scenario framing and map annotation, not as a hard constraint or validation target. GIS ZIP link is public but returned HTTP 202 in the workspace probe, so acquisition handling must be confirmed before relying on it. |
| Terrain / slope | [ELVIS access](https://elevation.fsdf.org.au/), [NSW Elevation and Depth guidance](https://www.nsw.gov.au/environment-land-and-water/spatial-data-and-mapping/foundation-spatial-data-framework/elevation-and-depth), and [Copernicus DEM GLO-30](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM) | ELVIS is the selected discovery/order path for Australian elevation products. The live NSW multi-CRS FeatureServer was also checked and exposes only SpotHeight, RelativeHeight, and Contour feature layers, not a raster DEM. Copernicus GLO-30 is the selected consistent lower-resolution fallback. | **Selected with explicit fallback.** `config/model.json` requires ELVIS/NSW first and Copernicus second. A local sidecar must identify source, artifact CRS, bounds CRS, resolution, complete coverage, nodata declaration, and acquisition date before selection. |
| Protected / managed land | [NSW National Parks and Wildlife Service Estate](https://data.nsw.gov.au/data/dataset/nsw-national-parks-and-wildlife-service-npws-estate3f9e7) and [live REST layer](https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/EDP/Estate/MapServer/0) | The layer covers NSW, is polygonal, exposes `NAME`, `TYPE`, `IUCN`, and related area/date fields, and is licensed CC BY. Live metadata reports EPSG:4283 and a full NSW extent. | **Selected as a penalty indicator.** Reproject to EPSG:7856 during processing. The owner did not approve a universal legal no-go rule; the dataset alone does not establish legal feasibility for this screening product. |
| Native vegetation | [NSW State Vegetation Type Map (SVTM)](https://data.nsw.gov.au/data/dataset/nsw-state-vegetation-type-map) and its [REST/WMS resources](https://mapprod3.environment.nsw.gov.au/arcgis/services/VIS/SVTM_NSW_Extant_PCT/MapServer/WMSServer) | Current release is C2.0.M2.2 (December 2025). The map is regional-scale, covers current PCT/vegetation class/formation, is available as ESRI quickview and 5m GeoTIFF, and is CC BY. | **Recommended as a weighted environmental penalty.** It is suitable for explaining native-vegetation trade-offs, but regional mapping uncertainty and the distinction between mapped vegetation and legal clearing controls must remain explicit. |
| Hydrography | [NSW Hydrography](https://data.nsw.gov.au/data/en/dataset/nsw-hydrography) and [ArcGIS REST service](https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Hydrography/MapServer) | Full-state service includes Hydroline, Named Watercourse, HydroArea, dams, lakes, swamps, and related features. Live metadata reports EPSG:3857; Named Watercourse is a group layer whose queryable child layers are 5 (small-scale) and 6 (large-scale). | **Recommended with reprojection and filtering.** Reproject to EPSG:7856 and use filtered watercourse/area requests. The bounded adapter uses object-ID pagination and fails clearly on incomplete responses; large feature volumes remain an operational consideration. |
| Roads and rail | [NSW Transport Theme multi-CRS service](https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Transport_Theme_multiCRS/FeatureServer), [Road Segment layer](https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Transport_Theme_multiCRS/FeatureServer/5), and [Railway layer](https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Transport_Theme_multiCRS/FeatureServer/7) | The official service includes road segments, railway, crossings, associated structures, and facilities. Live metadata reports EPSG:7844 and the expected road/rail layers. | **Recommended.** Treat road and railway intersections as assessment metrics and configurable crossing penalties, not automatic exclusions. Filter to the envelope and preserve source attributes such as type, name, surface, and on-type where available. |
| Optional regulatory sensitivity | [Biodiversity Values Map access guidance](https://www.environment.nsw.gov.au/topics/animals-and-plants/biodiversity-offsets-scheme/clear-and-develop-land/biodiversity-values-map-and-threshold-tool/seed-portal) and [live map service](https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/ePlanning/BiodiversityValuesMap/MapServer) | The map identifies high-biodiversity-value land used in the Biodiversity Offsets Scheme. The agency provides a service and geodatabase package but warns that the package is updated regularly and valid only on the download date. | **Do not include in the initial static core model.** Consider a dated contextual layer or sensitivity scenario after owner review. Its regulatory purpose and daily currency make it a poor unversioned optimization input. |

## Selected draft constraint set

The owner approved penalty treatment for this seven-component sensitivity model:

1. base route length / movement cost;
2. terrain difficulty derived from the selected DEM (for example slope);
3. protected or managed land from NPWS Estate;
4. native vegetation sensitivity from SVTM;
5. hydrography / watercourse crossing difficulty;
6. road crossing difficulty;
7. railway crossing difficulty.

Existing electricity infrastructure should initially remain contextual and support
endpoint selection. A proximity-to-existing-network cost can be considered later only
if the owner wants the study to represent a connection strategy rather than a neutral
new-corridor screen. Flood data and Biodiversity Values Map data should remain optional
until source versioning and methodological roles are approved.

## Source and methodological risks

- **Endpoint semantics:** a power station, substation, switching station, and proposed
  project endpoint are not interchangeable. The final pair must be named, sourced, and
  snapped consistently.
- **Coordinate reference systems:** several older NSW services are GDA94 or Web
  Mercator and are being retired. The pipeline should prefer GDA2020/multi-CRS service
  variants and record transformations.
- **Resolution and coverage:** 5m/2m elevation data may not be uniformly available in
  the candidate envelope. A consistent lower-resolution fallback is preferable to
  silently mixing products.
- **Environmental interpretation:** mapped protected land and native vegetation are
  screening indicators, not proof of legal feasibility or absence of species,
  heritage, tenure, geotechnical, or approval constraints.
- **Service behaviour:** NSW REST services are usable for targeted requests but should
  not be called as unbounded state-wide extraction jobs. Responses, source dates,
  schema, CRS, and feature counts need validation before derived outputs are accepted.
- **Terrain source capability:** the live NSW Elevation multi-CRS endpoint is a
  feature service without a raster DEM layer. ELVIS/NSW is therefore the selected
  primary acquisition path, with Copernicus GLO-30 as an explicit dated fallback.
- **Public project context:** EnergyCo's published corridor may change. It can help
  explain why the scenario matters, but it must not bias the optimizer or be presented
  as independent validation of a generated route.

## Resolved owner decisions and remaining review

The owner decisions that gated Priority 2 are resolved:

1. S1 is the portfolio study context.
2. The fixed endpoints use the reproducible public Bayswater and Eraring records.
3. Environmental and crossing factors are modeled as penalties/assessment metrics,
   not universal policy exclusions.

Priority 2 has an explicit approved sensitivity model in `docs/ANALYTICAL_MODEL.md`
and `config/model.json`. Final grid resolution, source coverage, and normalization
calibration remain implementation-validation work. Interactive user weighting is
deferred from the static MVP. Terrain source selection is approved; actual DEM
acquisition and raster processing remain Priority 3 work.
