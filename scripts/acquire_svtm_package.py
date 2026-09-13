#!/usr/bin/env python3
"""Acquire and structurally inspect the official Data.NSW/SEED SVTM ZIP package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ico_model.sources import write_manifest
from ico_model.svtm_package import (
    SvtmPackageError,
    download_svtm_package,
    inspect_svtm_zip,
    extract_svtm_members,
    validate_svtm_content_report,
    validate_persistent_path,
)


def load_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SvtmPackageError("model configuration must be an object")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/model.json"))
    parser.add_argument("--cache-dir", type=Path, default=Path("data/cache/seed/svtm-c2.0.m2.2"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/external/vectors/svtm-package"))
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--backoff", type=float, default=2.0)
    parser.add_argument(
        "--content-report",
        type=Path,
        help="reader-produced JSON report required to accept vector content into the model",
    )
    parser.add_argument(
        "--extract-member",
        action="append",
        help="explicit ZIP member to extract; repeat for sidecars, never extracts statewide data implicitly",
    )
    args = parser.parse_args()
    config = load_config(args.config)
    source = next(item for item in config["sources"] if item["id"] == "nsw-svtm")
    package = source.get("bulk_package")
    if not isinstance(package, dict):
        raise SvtmPackageError("nsw-svtm has no configured bulk_package")
    cache_dir = validate_persistent_path(args.cache_dir)
    output_dir = validate_persistent_path(args.output_dir)
    if cache_dir == output_dir or cache_dir in output_dir.parents or output_dir in cache_dir.parents:
        raise SvtmPackageError("SVTM package cache and output directories must be separate")
    archive = cache_dir / package["archive_filename"]
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Planned SVTM package cache: {cache_dir}")
    print(f"Planned SVTM package output: {output_dir}")
    print(f"SVTM package max archive bytes: {package['max_archive_bytes']}")
    print(f"SVTM package max working-set bytes: {package['max_working_set_bytes']}")
    download = download_svtm_package(
        package["url"],
        archive,
        max_archive_bytes=int(package["max_archive_bytes"]),
        timeout_seconds=args.timeout,
        max_retries=args.max_retries,
        backoff_seconds=args.backoff,
    )
    inspection = inspect_svtm_zip(
        archive,
        max_extracted_bytes=int(package["max_extracted_bytes"]),
        required_fields=tuple(package["required_fields"]),
    )
    extraction = None
    if args.extract_member:
        extraction = extract_svtm_members(
            archive,
            output_dir / "selected-members",
            args.extract_member,
            max_extracted_bytes=int(package["max_extracted_bytes"]),
            max_working_set_bytes=int(package["max_working_set_bytes"]),
        )
    content_validation = None
    if args.content_report is not None:
        content_report = json.loads(args.content_report.read_text(encoding="utf-8"))
        if not isinstance(content_report, dict):
            raise SvtmPackageError("SVTM content report must be a JSON object")
        content_validation = validate_svtm_content_report(
            content_report,
            required_fields=tuple(package["required_fields"]),
            expected_crs_epsg=int(source["service_crs_epsg"]),
            expected_feature_count=216808,
            expected_bounds=config["provisional_processing_envelope_gda2020"],
        )
    manifest = {
        "schema_version": 1,
        "format": "svtm-bulk-package-inspection",
        "scenario": config["scenario"],
        "source_id": source["id"],
        "dataset_id": package["dataset_id"],
        "resource_id": package["resource_id"],
        "release": package["release"],
        "license": package["license"],
        "source_url": package["url"],
        "download": download,
        "inspection": inspection,
        "extraction": extraction,
        "content_validation": content_validation,
        "analytical_acceptance": (
            "accepted-for-model-input" if content_validation else "pending-geospatial-schema-and-S1-coverage-validation"
        ),
    }
    manifest_path = output_dir / "svtm_package_manifest.json"
    write_manifest(manifest, manifest_path)
    print(f"Wrote SVTM package inspection manifest: {manifest_path}")
    if not inspection["vector_candidate_present"]:
        raise SvtmPackageError(
            "SVTM package contains no recognizable vector candidate; refusing to treat a "
            "symbology/documentation package as analytical vegetation data"
        )
    if content_validation is None:
        raise SvtmPackageError(
            "SVTM ZIP has a vector candidate but no content report; refusing to accept "
            "it until geometry, CRS, required attributes, S1 coverage, and REST reconciliation are verified"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, SvtmPackageError) as exc:
        raise SystemExit(f"SVTM package acquisition failed: {exc}") from exc
