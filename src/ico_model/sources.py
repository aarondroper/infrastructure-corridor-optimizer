"""Small, explicit source-acquisition helpers for public ArcGIS REST services."""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class SourceAccessError(RuntimeError):
    """Raised when a source cannot be fetched or returns an API error."""


class SourceValidationError(ValueError):
    """Raised when fetched source content cannot support the configured model."""


@dataclass(frozen=True)
class EndpointRecord:
    """Validated endpoint feature retained in a small provenance manifest."""

    role: str
    name: str
    source_object_id: int
    latitude: float
    longitude: float
    properties: dict[str, Any]
    geometry: Any

    def as_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "name": self.name,
            "source_object_id": self.source_object_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "properties": self.properties,
            "geometry": self.geometry,
        }


class ArcGISClient:
    """Fetch JSON from ArcGIS REST with bounded, identifiable requests."""

    def __init__(
        self,
        opener: Callable[..., Any] | None = None,
        *,
        timeout_seconds: float = 30.0,
        user_agent: str = "infrastructure-corridor-optimizer/0.1",
    ) -> None:
        if timeout_seconds <= 0 or not math.isfinite(timeout_seconds):
            raise ValueError("timeout_seconds must be finite and positive")
        self._opener = opener or urlopen
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent

    def fetch_json(
        self, url: str, params: Mapping[str, str | int | bool] | None = None
    ) -> dict[str, Any]:
        query = {key: str(value).lower() if isinstance(value, bool) else str(value)
                 for key, value in (params or {}).items()}
        query.setdefault("f", "json")
        separator = "&" if "?" in url else "?"
        request = Request(
            f"{url}{separator}{urlencode(query)}",
            headers={"User-Agent": self.user_agent, "Accept": "application/json"},
        )
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
        except HTTPError as exc:
            raise SourceAccessError(f"source returned HTTP {exc.code}: {url}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise SourceAccessError(f"source request failed: {url}: {exc}") from exc
        try:
            payload = json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
        except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SourceAccessError(f"source returned invalid JSON: {url}") from exc
        if not isinstance(payload, dict):
            raise SourceAccessError(f"source returned a non-object JSON response: {url}")
        if "error" in payload:
            raise SourceAccessError(f"ArcGIS reported an error for {url}: {payload['error']}")
        return payload

    def service_metadata(self, service_url: str) -> dict[str, Any]:
        return self.fetch_json(service_url)

    def query_features(
        self,
        layer_url: str,
        *,
        where: str,
        out_fields: Sequence[str] = ("*",),
        out_crs_epsg: int | None = None,
    ) -> list[dict[str, Any]]:
        payload = self.fetch_json(
            f"{layer_url.rstrip('/')}/query",
            {
                "where": where,
                "outFields": ",".join(out_fields),
                "returnGeometry": True,
                **({"outSR": out_crs_epsg} if out_crs_epsg else {}),
            },
        )
        features = payload.get("features")
        if not isinstance(features, list):
            raise SourceAccessError(f"ArcGIS query did not return a feature list: {layer_url}")
        return features


def _attribute(properties: Mapping[str, Any], *names: str) -> Any:
    lowered = {str(key).lower(): value for key, value in properties.items()}
    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return None


def _as_finite_float(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise SourceValidationError(f"endpoint field {field!r} is not numeric") from exc
    if not math.isfinite(number):
        raise SourceValidationError(f"endpoint field {field!r} is not finite")
    return number


def _feature_properties(feature: Mapping[str, Any]) -> dict[str, Any]:
    properties = feature.get("attributes", feature.get("properties"))
    if not isinstance(properties, dict):
        raise SourceValidationError("endpoint feature has no attribute object")
    return properties


def validate_service_crs(metadata: Mapping[str, Any], expected_epsg: int) -> None:
    spatial_reference = metadata.get("spatialReference", metadata.get("sourceSpatialReference"))
    if not isinstance(spatial_reference, Mapping):
        raise SourceValidationError("source service has no spatial reference metadata")
    observed = spatial_reference.get("latestWkid", spatial_reference.get("wkid"))
    if observed != expected_epsg:
        raise SourceValidationError(
            f"source CRS mismatch: expected EPSG:{expected_epsg}, observed {observed!r}"
        )


def summarize_arcgis_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Extract stable topology/CRS/extent facts from an ArcGIS service response."""

    spatial_reference = metadata.get("spatialReference", metadata.get("sourceSpatialReference"))
    if not isinstance(spatial_reference, Mapping):
        raise SourceValidationError("ArcGIS metadata has no spatial reference")
    observed_epsg = spatial_reference.get("latestWkid", spatial_reference.get("wkid"))
    layers = metadata.get("layers")
    if isinstance(layers, list):
        layer_summary = [
            {
                key: layer[key]
                for key in ("id", "name", "type", "geometryType", "parentLayerId")
                if key in layer
            }
            for layer in layers
            if isinstance(layer, Mapping)
        ]
    elif "id" in metadata and "name" in metadata:
        layer_summary = [
            {
                key: metadata[key]
                for key in ("id", "name", "type", "geometryType")
                if key in metadata
            }
        ]
    else:
        layer_summary = []
    extent = metadata.get("fullExtent", metadata.get("extent"))
    return {
        "current_version": metadata.get("currentVersion"),
        "service_description": metadata.get("serviceDescription", metadata.get("description", "")),
        "crs_epsg": observed_epsg,
        "full_extent": extent,
        "layers": layer_summary,
    }


def validate_expected_layers(
    metadata_summary: Mapping[str, Any], expected_layers: Sequence[Mapping[str, Any]]
) -> None:
    """Require configured source layer IDs/names/types to exist in metadata."""

    available = {layer.get("id"): layer for layer in metadata_summary.get("layers", [])}
    for expected in expected_layers:
        layer = available.get(expected.get("id"))
        if layer is None or layer.get("name") != expected.get("name"):
            raise SourceValidationError(
                f"expected ArcGIS layer is unavailable or renamed: {expected}"
            )
        expected_geometry = expected.get("geometry_type")
        if expected_geometry and layer.get("geometryType") != expected_geometry:
            raise SourceValidationError(
                f"ArcGIS layer geometry mismatch for {expected['name']!r}: "
                f"expected {expected_geometry!r}, observed {layer.get('geometryType')!r}"
            )


def validate_expected_layer_names(
    metadata_summary: Mapping[str, Any], expected_names: Sequence[str]
) -> None:
    """Require configured layer names to be present in an ArcGIS metadata summary."""

    available_names = {layer.get("name") for layer in metadata_summary.get("layers", [])}
    missing = sorted(set(expected_names) - available_names)
    if missing:
        raise SourceValidationError(f"expected ArcGIS layers are unavailable or renamed: {missing}")


def validate_required_layer_type(metadata_summary: Mapping[str, Any], expected_type: str) -> None:
    """Require at least one layer of a configured ArcGIS type."""

    if not any(layer.get("type") == expected_type for layer in metadata_summary.get("layers", [])):
        observed = sorted({layer.get("type") for layer in metadata_summary.get("layers", [])})
        raise SourceValidationError(
            f"required ArcGIS layer type {expected_type!r} is unavailable; observed {observed}"
        )


def validate_endpoint_features(
    configured_endpoints: Mapping[str, Mapping[str, Any]],
    features: Sequence[Mapping[str, Any]],
    *,
    coordinate_tolerance: float = 1e-5,
) -> list[EndpointRecord]:
    """Validate configured endpoint identity and return manifest-ready records."""

    if coordinate_tolerance <= 0 or not math.isfinite(coordinate_tolerance):
        raise ValueError("coordinate_tolerance must be finite and positive")
    by_id: dict[int, Mapping[str, Any]] = {}
    for feature in features:
        properties = _feature_properties(feature)
        object_id = _attribute(properties, "objectid", "fid", "id")
        try:
            object_id_int = int(object_id)
        except (TypeError, ValueError) as exc:
            raise SourceValidationError("endpoint feature has no integer object ID") from exc
        if object_id_int in by_id:
            raise SourceValidationError(f"duplicate endpoint object ID returned: {object_id_int}")
        by_id[object_id_int] = feature

    validated: list[EndpointRecord] = []
    for role, expected in configured_endpoints.items():
        try:
            object_id = int(expected["source_object_id"])
            feature = by_id[object_id]
        except (KeyError, TypeError, ValueError) as exc:
            raise SourceValidationError(
                f"configured endpoint {role!r} object ID is missing from source response"
            ) from exc
        properties = _feature_properties(feature)
        actual_name = _attribute(properties, "feature_name", "name")
        if actual_name != expected["name"]:
            raise SourceValidationError(
                f"endpoint {role!r} name mismatch: expected {expected['name']!r}, "
                f"observed {actual_name!r}"
            )
        actual_state = _attribute(properties, "state")
        if actual_state != expected["state"]:
            raise SourceValidationError(
                f"endpoint {role!r} state mismatch: expected {expected['state']!r}, "
                f"observed {actual_state!r}"
            )
        latitude = _as_finite_float(_attribute(properties, "latitude", "lat"), "latitude")
        longitude = _as_finite_float(_attribute(properties, "longitude", "lon"), "longitude")
        if abs(latitude - float(expected["latitude"])) > coordinate_tolerance or abs(
            longitude - float(expected["longitude"])
        ) > coordinate_tolerance:
            raise SourceValidationError(f"endpoint {role!r} coordinates differ from configuration")
        validated.append(
            EndpointRecord(
                role=role,
                name=str(expected["name"]),
                source_object_id=object_id,
                latitude=latitude,
                longitude=longitude,
                properties=dict(properties),
                geometry=feature.get("geometry"),
            )
        )
    return validated


def build_endpoint_manifest(
    config: Mapping[str, Any],
    source_metadata: Mapping[str, Any],
    query: Mapping[str, Any],
    endpoints: Sequence[EndpointRecord],
) -> dict[str, Any]:
    """Create a provenance manifest after all endpoint validation succeeds."""

    source = next(
        source for source in config["sources"] if source["id"] == query["source_id"]
    )
    metadata = {
        key: source_metadata[key]
        for key in ("currentVersion", "fullVersion", "serviceDescription", "spatialReference")
        if key in source_metadata
    }
    return {
        "schema_version": 1,
        "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
        "scenario": config["scenario"],
        "source": {
            "id": source["id"],
            "url": source["url"],
            "layer_id": source["layer_id"],
            "crs_epsg": source["crs_epsg"],
            "metadata": metadata,
            "query": dict(query),
        },
        "endpoints": [endpoint.as_dict() for endpoint in endpoints],
    }


def write_manifest(manifest: Mapping[str, Any], output_path: str | Path) -> None:
    """Write a validated manifest atomically enough for a single-file CLI output."""

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    temporary.replace(destination)
