"""Probe configured ArcGIS source topology and coverage metadata."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from ico_model.config import ConfigError, load_config
from ico_model.sources import (
    ArcGISClient,
    SourceAccessError,
    SourceValidationError,
    summarize_arcgis_metadata,
    validate_expected_layers,
    validate_expected_layer_names,
    validate_required_layer_type,
    write_manifest,
)


def probe(config: dict, client: ArcGISClient) -> dict:
    records = []
    failures = []
    for source in config["sources"]:
        access = source.get("access")
        record = {"id": source["id"], "url": source["url"], "access": access}
        if source.get("role") == "planning context only":
            record.update({"status": "context-only", "reason": "not an API metadata source"})
        elif access == "WMS":
            record.update({"status": "deferred", "reason": "WMS capabilities probe not implemented"})
        elif access == "ArcGIS REST":
            try:
                metadata = client.service_metadata(source["url"])
                summary = summarize_arcgis_metadata(metadata)
                expected_layers = source.get("expected_layers")
                if expected_layers:
                    validate_expected_layers(summary, expected_layers)
                expected_layer_names = source.get("expected_layer_names")
                if expected_layer_names:
                    validate_expected_layer_names(summary, expected_layer_names)
                expected_layer = source.get("expected_layer")
                if expected_layer:
                    validate_expected_layers(summary, [expected_layer])
                required_layer_type = source.get("required_layer_type")
                if required_layer_type:
                    validate_required_layer_type(summary, required_layer_type)
                record.update({"status": "validated", "metadata": summary})
            except (SourceAccessError, SourceValidationError) as exc:
                record.update({"status": "failed", "error": str(exc)})
                failures.append(source["id"])
        else:
            record.update({"status": "deferred", "reason": "unsupported access type"})
        records.append(record)
    return {
        "schema_version": 1,
        "probed_at_utc": datetime.now(timezone.utc).isoformat(),
        "scenario": config["scenario"],
        "processing_envelope": config["provisional_processing_envelope_gda2020"],
        "records": records,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/model.json"))
    parser.add_argument("--output", type=Path, default=Path("data/source_probe.json"))
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()
    report = probe(load_config(args.config), ArcGISClient(timeout_seconds=args.timeout))
    write_manifest(report, args.output)
    print(f"Wrote source probe report: {args.output}")
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ConfigError, SourceAccessError, SourceValidationError) as exc:
        raise SystemExit(f"Source probe failed: {exc}") from exc
