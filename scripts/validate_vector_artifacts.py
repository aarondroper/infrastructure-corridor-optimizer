#!/usr/bin/env python3
"""Validate an external bounded ArcGIS vector acquisition manifest and artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ico_model.sources import SourceAccessError, SourceValidationError, write_manifest
from ico_model.vector_artifacts import validate_vector_manifest


def load_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SourceValidationError("model configuration must be a JSON object")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("config/model.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    report = validate_vector_manifest(
        args.manifest,
        expected_scenario=config["scenario"],
        expected_output_crs_epsg=config["analysis_crs_epsg"],
    )
    write_manifest(report, args.output)
    print(f"Wrote vector artifact validation report: {args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, TypeError, ValueError, SourceAccessError, SourceValidationError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Vector artifact validation failed: {exc}") from exc
