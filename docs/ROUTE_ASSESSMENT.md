# S1 Route Assessment and Preset Calibration Review

## Evidence basis

This review uses the independently generated assessments in
`data/external/routes/s1-100m/route_assessments.json` and the compact application
asset derived from them. It does not change the approved weights, exclusions,
penalty interpretation, or preset definitions. Route lengths are geodesic lengths
of the published EPSG:7844 centerlines; vegetation counts are 100 m route-cell
samples from the validated C2.0.M2.2 classified SVTM raster.

## Physical comparison

| Preset | Length (km) | Mean / max slope (°) | Protected areas | Native vegetation cells / fraction | Hydroline crossings | Hydroarea interactions | Major-road crossings | Railway crossings |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Shortest | 95.76 | 2.76 / 30.05 | 1 | 136 / 18.6% | 120 | 18 | 16 | 4 |
| Balanced | 96.28 | 2.67 / 33.48 | 1 | 113 / 15.2% | 117 | 17 | 17 | 4 |
| Environmental | 99.17 | 2.69 / 33.48 | 1 | 82 / 10.4% | 104 | 19 | 20 | 4 |

Additional diagnostic values:

| Preset | Route cells | Terrain normalized mean | All road features | Unique SVTM classes | Unavailable cells | Grid-boundary cells |
|---|---:|---:|---:|---:|---:|---:|
| Shortest | 732 | 0.1350 | 136 | 29 | 0 | 0 |
| Balanced | 741 | 0.1321 | 134 | 26 | 0 | 0 |
| Environmental | 786 | 0.1328 | 145 | 23 | 0 | 0 |

All three routes use the same validated endpoint cells, have simple centerlines,
and pass the availability and continuity checks. Endpoint snap offsets are common
to the routes: approximately 67.6 m at Bayswater and 47.3 m at Eraring.

## Interpretation

- **Shortest** behaves credibly as the length-focused baseline: it is the shortest
  route and has the lowest major-road count, but it has the highest native-vegetation
  cell count and hydroline crossing count.
- **Balanced** behaves credibly as a modest compromise: it adds only 0.53 km
  (0.55%) to the shortest route, reduces native-vegetation cells by 16.9% and
  hydroline crossings by 2.5%, and has the lowest mean slope. Its maximum slope is
  higher than Shortest, and it adds one major-road crossing.
- **Environmental** behaves credibly in its strongest intended direction: it adds
  3.41 km (3.56%) and reduces native-vegetation cells by 39.7% and hydroline
  crossings by 13.3% relative to Shortest. It does not reduce the count of
  intersected protected-area features, increases hydroarea interactions by one,
  and has more road crossings. Those results are consistent with the current
  environmental preset's relative emphasis and with the coarse source indicators;
  they do not by themselves justify changing the model.

### Calibration classification

**Classification 1 — presets behave credibly as intended; no calibration is
currently justified.** The observed differences are directionally consistent with
the approved sensitivity profiles, while the remaining counter-signals are small
or explainable by metric coverage and resolution. Future calibration can be
revisited after owner review of a broader scenario set, but this verification
milestone does not create an owner-level methodology decision.

## Interpretation limits and grid artifacts

- The routes are centerlines through 100 m grid cells, not surveyed alignments;
  diagonal and direction-change statistics describe grid behavior rather than
  constructible geometry. The diagonal-step fractions are 74.8%, 72.7%, and
  63.6% for Shortest, Balanced, and Environmental respectively.
- Native-vegetation interaction is sampled at route-cell centers from the 5 m
  classified package product after reprojection/resampling. It is not a corridor
  footprint or an ecological impact estimate.
- Feature counts are intersected source records. Segmented hydrography, roads, and
  rail layers may produce multiple records for one named physical crossing.
- The protected-area source yields one intersected feature for all three routes,
  so that metric has no discriminating power in this S1 envelope. Similarly, all
  routes cross four railway records. These are source/envelope limitations, not
  evidence that the environmental preset is ineffective.
- The `weighted_cell_exposure` values are descriptive sums under different preset
  weights and should not be compared as if they were a common physical unit. The
  table above is the calibration evidence.
