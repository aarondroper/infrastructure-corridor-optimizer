#!/usr/bin/env python3
"""List or remove abandoned acquisition cache namespaces and staging directories."""

from __future__ import annotations

import argparse
import tempfile
import shutil
import time
from pathlib import Path


def _safe_root(path: Path) -> Path:
    root = path.resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    transient_roots = (temp_root, Path("/var/tmp"), Path("/dev/shm"))
    if any(root == transient or transient in root.parents for transient in transient_roots):
        raise ValueError(f"refusing cleanup under system temporary storage: {root}")
    return root


def _candidates(root: Path, older_than_seconds: float, *, staging_only: bool) -> list[Path]:
    now = time.time()
    if not root.is_dir():
        return []
    return sorted(
        child
        for child in root.iterdir()
        if child.is_dir()
        and (
            child.name.startswith(".staging-")
            if staging_only
            else not child.name.startswith(".")
        )
        and now - child.stat().st_mtime >= older_than_seconds
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=Path("data/cache/arcgis"))
    parser.add_argument("--output-root", type=Path, default=Path("data/external/vectors"))
    parser.add_argument("--older-than-hours", type=float, default=24.0)
    parser.add_argument("--delete", action="store_true", help="delete listed candidates")
    args = parser.parse_args()
    if args.older_than_hours < 0:
        raise ValueError("--older-than-hours must be non-negative")
    roots = [_safe_root(args.cache_dir), _safe_root(args.output_root)]
    candidates = []
    for root in roots:
        candidates.extend(
            _candidates(
                root,
                args.older_than_hours * 3600,
                staging_only=root == roots[1],
            )
        )
    for path in candidates:
        action = "removing" if args.delete else "would remove"
        print(f"{action} {path}")
        if args.delete:
            shutil.rmtree(path)
    if not candidates:
        print("No abandoned acquisition directories matched the cleanup criteria.")
    if not args.delete:
        print("Dry run only; pass --delete after confirming the listed paths.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        raise SystemExit(f"Acquisition cleanup failed: {exc}") from exc
