# Configure SVTM Native-Vegetation Acquisition

## Objective

Make the approved NSW State Vegetation Type Map source usable by the bounded
ArcGIS acquisition boundary while preserving the current WMS resource for display
and documenting the scale of the resulting external capture.

## Outcome

Configured `nsw-svtm` in `config/model.json` to use the queryable
`Plant Community Type with labels` polygon layer (layer 3), EPSG:3308 service
metadata, a 1,000-ID page policy, and explicit PCT/vegetation class/form fields.
The WMS display resource remains recorded separately. The existing acquisition
boundary can select and validate this layer, and the live topology probe validates
the service and expected layer.

A live count within the configured S1 envelope returned approximately 216,808
intersecting polygons. No full artifact was published: high-volume service
responsiveness and complete staged capture still require a dedicated external run.
A small live capture also encountered an ArcGIS 500 error when requesting a larger
object-ID batch, while smaller samples succeeded; the page policy therefore remains
unverified for a complete run.

## Validation

- 50 standard-library unit tests passed, including configuration and fake-client
  acquisition coverage for the SVTM layer.
- Configuration JSON and `git diff --check` passed.
- Live `scripts/probe_sources.py` validation passed for SVTM at EPSG:3308 and for
  the other configured ArcGIS sources.
- Live count query confirmed the expected high-volume S1 envelope scope.
- Small live feature queries confirmed the PCT fields and EPSG:7856 output for
  successful responses, but did not establish a complete capture strategy.

## Follow-up

Attempt a controlled, resumable or otherwise operationally bounded full SVTM
materialization before using it in geographic cost derivation. Keep the output
external to Git and validate its manifest before downstream processing.
