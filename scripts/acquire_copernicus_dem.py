"""Acquire the configured public Copernicus GLO-30 fallback tiles for S1."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from ico_model.config import load_config
from ico_model.dem_acquisition import DemAcquisitionError, acquire_copernicus_tiles


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/model.json"))
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/external/dem/copernicus-glo30-s1")
    )
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--backoff", type=float, default=1.0)
    parser.add_argument("--max-tiles", type=int, default=16)
    parser.add_argument("--max-total-bytes", type=int, default=300_000_000)
    parser.add_argument(
        "--allow-temporary-path",
        action="store_true",
        help="allow --output-dir under the system temporary directory for bounded probes",
    )
    args = parser.parse_args()
    config = load_config(args.config)
    output_path = args.output_dir.resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    transient_roots = (temp_root, Path("/var/tmp"), Path("/dev/shm"))
    if not args.allow_temporary_path and any(
        output_path == root or root in output_path.parents for root in transient_roots
    ):
        raise DemAcquisitionError(
            "refusing system temporary DEM output path; use persistent data storage "
            "or --allow-temporary-path for a bounded probe"
        )
    policy = config.get("terrain_source_policy")
    if not isinstance(policy, dict):
        raise DemAcquisitionError("configuration has no terrain_source_policy")
    source_id = policy.get("fallback_source_id")
    if not isinstance(source_id, str):
        raise DemAcquisitionError("terrain policy has no fallback source")
    print(f"Planned DEM output: {output_path}")
    print("DEM temporary downloads are created beside each destination tile and removed after replacement.")
    manifest = acquire_copernicus_tiles(
        policy["required_processing_envelope"],
        args.output_dir,
        source_id=source_id,
        timeout_seconds=args.timeout,
        max_retries=args.max_retries,
        backoff_seconds=args.backoff,
        max_tiles=args.max_tiles,
        max_total_bytes=args.max_total_bytes,
    )
    print(f"Acquired Copernicus GLO-30 tile set: {manifest}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, DemAcquisitionError) as exc:
        raise SystemExit(f"Copernicus DEM acquisition failed: {exc}") from exc
