"""Acquire and validate the configured S1 endpoint source records."""

from __future__ import annotations

import argparse
from pathlib import Path

from ico_model.config import ConfigError, load_config
from ico_model.sources import (
    ArcGISClient,
    SourceAccessError,
    SourceValidationError,
    build_endpoint_manifest,
    validate_endpoint_features,
    validate_service_crs,
    write_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("config/model.json"), help="model configuration path"
    )
    parser.add_argument(
        "--output", type=Path, default=Path("data/source_manifest.json"), help="manifest output path"
    )
    parser.add_argument("--timeout", type=float, default=30.0, help="request timeout in seconds")
    args = parser.parse_args()

    config = load_config(args.config)
    source = next(source for source in config["sources"] if source["id"] == "ga-electricity-infrastructure")
    service_url = source["url"]
    layer_url = f"{service_url.rstrip('/')}/{source['layer_id']}"
    object_ids = [config["endpoints"][role]["source_object_id"] for role in ("origin", "destination")]
    where = f"objectid IN ({','.join(str(object_id) for object_id in object_ids)})"

    client = ArcGISClient(timeout_seconds=args.timeout)
    metadata = client.service_metadata(service_url)
    validate_service_crs(metadata, source["crs_epsg"])
    features = client.query_features(
        layer_url,
        where=where,
        out_fields=("OBJECTID", "feature_name", "state", "latitude", "longitude"),
        out_crs_epsg=source["crs_epsg"],
    )
    endpoints = validate_endpoint_features(config["endpoints"], features)
    manifest = build_endpoint_manifest(
        config,
        metadata,
        {"source_id": source["id"], "where": where, "out_crs_epsg": source["crs_epsg"]},
        endpoints,
    )
    write_manifest(manifest, args.output)
    print(f"Wrote validated endpoint manifest: {args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ConfigError, SourceAccessError, SourceValidationError) as exc:
        raise SystemExit(f"Source acquisition failed: {exc}") from exc
