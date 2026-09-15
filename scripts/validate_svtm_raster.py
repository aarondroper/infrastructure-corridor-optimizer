"""Validate the official SVTM classified raster and materialize only S1."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from ico_model.config import load_config
from ico_model.svtm_package import inspect_svtm_zip
from ico_model.svtm_raster import SvtmRasterError, validate_and_materialize_s1_raster, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("config/model.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/external/vectors/svtm-package"))
    parser.add_argument("--cell-size-m", type=float, default=100.0)
    args = parser.parse_args()
    config = load_config(args.config)
    source = next(item for item in config["sources"] if item["id"] == "nsw-svtm")
    package = source["bulk_package"]
    output_dir = args.output_dir.resolve()
    if any(root == output_dir or root in output_dir.parents for root in (Path("/tmp"), Path("/var/tmp"), Path("/dev/shm"))):
        raise SvtmRasterError(f"refusing SVTM output under transient path: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("CPL_TMPDIR", str(output_dir))
    os.environ.setdefault("GDAL_CACHEMAX", "64")
    print(f"SVTM archive: {args.archive.resolve()}")
    print(f"SVTM persistent output: {output_dir}")
    inspection = inspect_svtm_zip(
        args.archive,
        max_extracted_bytes=package["max_extracted_bytes"],
        required_fields=("PCTID", "PCTName", "vegClass", "vegForm"),
    )
    inspection["archive_limit_bytes"] = package["max_archive_bytes"]
    inspection["archive_limit_exceeded"] = inspection["archive_bytes"] > package["max_archive_bytes"]
    report = validate_and_materialize_s1_raster(
        args.archive,
        output_dir / f"s1-svtm-{int(args.cell_size_m)}m.tif",
        config["provisional_processing_envelope_gda2020"],
        target_resolution_m=args.cell_size_m,
        expected_archive_sha256=inspection["archive_sha256"],
    )
    content_report_path = output_dir / "s1-svtm-raster-content-report.json"
    write_json(content_report_path, report)
    manifest = {
        "schema_version": 1,
        "format": "svtm-s1-classified-raster",
        "scenario": config["scenario"],
        "source_id": "nsw-svtm",
        "dataset_id": package["dataset_id"],
        "resource_id": package["resource_id"],
        "source_url": package["url"],
        "release": "C2.0.M2.2",
        "license": "Creative Commons Attribution",
        "archive_safety": {
            "configured_max_archive_bytes": package["max_archive_bytes"],
            "archive_limit_exceeded": inspection["archive_limit_exceeded"],
            "configured_max_extracted_bytes": package["max_extracted_bytes"],
            "full_package_extraction_limit_exceeded": inspection["extracted_limit_exceeded"],
            "configured_max_working_set_bytes": package["max_working_set_bytes"],
            "materialization_mode": "direct-window-read-from-vsizip",
        },
        "archive": inspection,
        "content_validation": report,
        "analytical_acceptance": "accepted-for-model-input",
        "artifact_path": str((output_dir / f"s1-svtm-{int(args.cell_size_m)}m.tif").resolve()),
        "content_report_path": str(content_report_path.resolve()),
        "observed_persistent_working_set_bytes": args.archive.stat().st_size
        + (output_dir / f"s1-svtm-{int(args.cell_size_m)}m.tif").stat().st_size
        + content_report_path.stat().st_size,
    }
    manifest_path = output_dir / "svtm_s1_raster_manifest.json"
    write_json(manifest_path, manifest)
    print(f"Wrote S1 SVTM raster: {manifest['artifact_path']}")
    print(f"Wrote SVTM content report: {content_report_path}")
    print(f"Wrote SVTM provenance manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, SvtmRasterError) as exc:
        raise SystemExit(f"SVTM raster validation failed: {exc}") from exc
