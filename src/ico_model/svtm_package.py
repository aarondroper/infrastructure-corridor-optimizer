"""Guarded acquisition and structural validation for the official SVTM ZIP package."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import time
import zipfile
from collections.abc import Callable, Mapping
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class SvtmPackageError(RuntimeError):
    """Raised when the official SVTM package cannot be safely acquired or inspected."""


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def validate_persistent_path(path: str | Path, *, allow_temporary: bool = False) -> Path:
    """Reject package roots that would place large files in transient storage."""

    resolved = Path(path).resolve()
    if allow_temporary:
        return resolved
    transient_roots = {
        Path(os.getenv("TMPDIR", "/tmp")).resolve(),
        Path("/tmp").resolve(),
        Path("/var/tmp").resolve(),
        Path("/dev/shm").resolve(),
    }
    if any(resolved == root or root in resolved.parents for root in transient_roots):
        raise SvtmPackageError(
            f"refusing SVTM package storage under transient path {resolved}; "
            "use an explicit persistent project path"
        )
    return resolved


def _safe_member_name(name: str) -> None:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name:
        raise SvtmPackageError(f"ZIP member has unsafe path: {name!r}")


def _is_symlink(info: zipfile.ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0xFFFF
    return stat.S_IFMT(mode) == stat.S_IFLNK


def inspect_svtm_zip(
    archive_path: str | Path,
    *,
    max_members: int = 100_000,
    max_extracted_bytes: int = 8_000_000_000,
    required_fields: tuple[str, ...] = (
        "OBJECTID",
        "PCTID",
        "PCTName",
        "vegClass",
        "vegForm",
    ),
) -> dict[str, Any]:
    """Inspect a complete ZIP without extracting it or trusting its filename."""

    archive = Path(archive_path)
    if not archive.is_file():
        raise SvtmPackageError(f"SVTM package archive is missing: {archive}")
    try:
        digest = hashlib.sha256()
        with archive.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        with zipfile.ZipFile(archive) as package:
            infos = package.infolist()
            if len(infos) > max_members:
                raise SvtmPackageError(
                    f"SVTM package has too many members: {len(infos)} > {max_members}"
                )
            extracted_bytes = 0
            compressed_bytes = 0
            extracted_limit_exceeded = False
            member_names: list[str] = []
            vector_members: list[str] = []
            for info in infos:
                _safe_member_name(info.filename)
                if _is_symlink(info):
                    raise SvtmPackageError(f"SVTM package contains a symlink: {info.filename}")
                extracted_bytes += info.file_size
                compressed_bytes += info.compress_size
                if extracted_bytes > max_extracted_bytes:
                    # Inventory is safe because it reads only ZIP metadata. The
                    # selected-materialization path enforces the limit before
                    # writing any member, and records this full-package overage.
                    extracted_limit_exceeded = True
                member_names.append(info.filename)
                lower = info.filename.lower()
                if (
                    lower.endswith((".shp", ".gpkg", ".geojson"))
                    or (
                        lower.endswith(".json")
                        and any(token in lower for token in ("feature", "vegetation", "pct", "svtm"))
                    )
                    or ".gdb/" in lower
                    or lower.endswith(".gdb")
                ):
                    vector_members.append(info.filename)
            bad_member = package.testzip()
            if bad_member is not None:
                raise SvtmPackageError(f"SVTM package CRC validation failed: {bad_member}")
    except (OSError, zipfile.BadZipFile) as exc:
        raise SvtmPackageError(f"SVTM package is not a readable ZIP: {archive}") from exc

    lower_names = [name.lower() for name in member_names]
    documentation_members = [
        name
        for name in member_names
        if name.lower().endswith((".mxd", ".lyr", ".lyrx", ".pdf", ".txt", ".xml"))
    ]
    return {
        "archive_path": str(archive.resolve()),
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": digest.hexdigest(),
        "member_count": len(member_names),
        "compressed_member_bytes": compressed_bytes,
        "extracted_member_bytes": extracted_bytes,
        "member_names": member_names,
        "vector_members": vector_members,
        "documentation_members": documentation_members,
        "crc_status": "all-members-valid",
        "required_fields": list(required_fields),
        "extracted_limit_bytes": max_extracted_bytes,
        "extracted_limit_exceeded": extracted_limit_exceeded,
        "vector_candidate_present": bool(vector_members),
        "analytical_content_status": (
            "vector-candidate-requires-geospatial-schema-validation"
            if vector_members
            else "no-vector-candidate-package-may-be-symbology-only"
        ),
        "observed_member_name_count": len(lower_names),
    }


def validate_svtm_content_report(
    report: Mapping[str, Any],
    *,
    required_fields: tuple[str, ...],
    expected_crs_epsg: int = 3308,
    expected_feature_count: int | None = None,
    expected_bounds: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """Validate a reader-produced report before package data can enter the model."""

    if report.get("coverage_status") != "complete":
        raise SvtmPackageError("SVTM package content report is not complete")
    if report.get("coverage_scope") != "configured-S1-envelope":
        raise SvtmPackageError(
            "SVTM package content report is not scoped to the configured S1 envelope"
        )
    geometry_type = str(report.get("geometry_type", "")).lower()
    representation = str(report.get("representation", "vector")).lower()
    if representation == "vector" and "polygon" not in geometry_type:
        raise SvtmPackageError(f"SVTM package content is not polygonal: {geometry_type!r}")
    if representation == "classified-raster" and "raster" not in geometry_type:
        raise SvtmPackageError(f"SVTM package content is not raster data: {geometry_type!r}")
    try:
        crs_epsg = int(report["crs_epsg"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SvtmPackageError("SVTM package content report lacks CRS") from exc
    if crs_epsg != expected_crs_epsg:
        raise SvtmPackageError(
            f"SVTM package CRS mismatch: expected EPSG:{expected_crs_epsg}, observed EPSG:{crs_epsg}"
        )
    if representation == "vector":
        try:
            feature_count = int(report["feature_count"])
            unique_id_count = int(report["unique_id_count"])
            duplicate_id_count = int(report["duplicate_id_count"])
        except (KeyError, TypeError, ValueError) as exc:
            raise SvtmPackageError(
                "SVTM vector report lacks feature or ID reconciliation counts"
            ) from exc
        if feature_count <= 0:
            raise SvtmPackageError("SVTM package content has no features")
        if unique_id_count != feature_count or duplicate_id_count != 0:
            raise SvtmPackageError(
                "SVTM package content has duplicate or unreconciled feature IDs: "
                f"features={feature_count}, unique={unique_id_count}, duplicates={duplicate_id_count}"
            )
        if report.get("rest_count_reconciled") is not True:
            raise SvtmPackageError("SVTM package content report does not reconcile with REST count evidence")
    elif representation == "classified-raster":
        try:
            raster_width = int(report["raster_width"])
            raster_height = int(report["raster_height"])
            resolution_m = float(report["resolution_m"])
            nodata_value = int(report["nodata_value"])
        except (KeyError, TypeError, ValueError) as exc:
            raise SvtmPackageError(
                "SVTM raster report lacks dimensions, resolution, or nodata"
            ) from exc
        if raster_width <= 0 or raster_height <= 0 or resolution_m <= 0:
            raise SvtmPackageError("SVTM raster dimensions or resolution are invalid")
        if report.get("rest_count_reconciled") != "not-applicable-raster-representation":
            raise SvtmPackageError(
                "SVTM raster report must explicitly explain why REST feature-count reconciliation is not applicable"
            )
        value_table_fields = report.get("value_table_fields")
        missing = [field for field in required_fields if field.lower() not in {
            str(value).lower() for value in value_table_fields or []
        }]
        if not isinstance(value_table_fields, list) or missing:
            raise SvtmPackageError(
                f"SVTM raster value table is missing required fields: {missing}"
            )
    else:
        raise SvtmPackageError(f"unsupported SVTM content representation: {representation}")
    fields = report.get("fields")
    if representation == "classified-raster" and fields is None:
        fields = report.get("value_table_fields")
    if not isinstance(fields, list):
        raise SvtmPackageError("SVTM package content report has no field list")
    field_names = {str(field).lower() for field in fields}
    missing = [field for field in required_fields if field.lower() not in field_names]
    if missing:
        raise SvtmPackageError(f"SVTM package is missing required fields: {missing}")
    bounds = report.get("bounds")
    if expected_bounds is not None:
        if not isinstance(bounds, Mapping):
            raise SvtmPackageError("SVTM package content report has no bounds")
        for key in ("west", "south", "east", "north"):
            try:
                if key in ("west", "south"):
                    valid = float(bounds[key]) <= float(expected_bounds[key])
                else:
                    valid = float(bounds[key]) >= float(expected_bounds[key])
            except (KeyError, TypeError, ValueError) as exc:
                raise SvtmPackageError("SVTM package content bounds are invalid") from exc
            if not valid:
                raise SvtmPackageError("SVTM package content does not cover the S1 envelope")
    if (
        representation == "vector"
        and expected_feature_count is not None
        and feature_count != expected_feature_count
    ):
        raise SvtmPackageError(
            f"SVTM package feature count does not reconcile with REST evidence: "
            f"{feature_count} != {expected_feature_count}"
        )
    return {
        "coverage_status": "complete",
        "geometry_type": geometry_type,
        "crs_epsg": crs_epsg,
        "representation": representation,
        "feature_count": feature_count if representation == "vector" else None,
        "unique_id_count": unique_id_count if representation == "vector" else None,
        "duplicate_id_count": duplicate_id_count if representation == "vector" else None,
        "rest_count_reconciled": report.get("rest_count_reconciled"),
        "coverage_scope": "configured-S1-envelope",
        "fields": list(fields),
        "bounds": dict(bounds) if isinstance(bounds, Mapping) else None,
        **(
            {
                "raster_width": raster_width,
                "raster_height": raster_height,
                "resolution_m": resolution_m,
                "nodata_value": nodata_value,
                "value_table_fields": list(value_table_fields),
            }
            if representation == "classified-raster"
            else {}
        ),
    }


def extract_svtm_members(
    archive_path: str | Path,
    output_dir: str | Path,
    member_names: list[str],
    *,
    max_extracted_bytes: int = 8_000_000_000,
    max_working_set_bytes: int | None = None,
    allow_temporary: bool = False,
) -> dict[str, Any]:
    """Atomically extract an explicitly selected member list, never the whole ZIP implicitly."""

    if not member_names:
        raise SvtmPackageError("no SVTM ZIP members were selected for extraction")
    archive = Path(archive_path).resolve()
    archive_bytes = archive.stat().st_size
    if max_working_set_bytes is not None and max_working_set_bytes <= 0:
        raise ValueError("max_working_set_bytes must be positive when supplied")
    if max_working_set_bytes is not None and archive_bytes > max_working_set_bytes:
        raise SvtmPackageError(
            f"SVTM archive already exceeds working-set limit: "
            f"{archive_bytes} > {max_working_set_bytes}"
        )
    destination = validate_persistent_path(output_dir, allow_temporary=allow_temporary)
    if destination.exists() and any(destination.iterdir()):
        raise SvtmPackageError(f"SVTM extraction output must be empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".staging-svtm-", dir=destination.parent))
    selected = set(member_names)
    extracted_bytes = 0
    try:
        with zipfile.ZipFile(archive) as package:
            info_by_name = {info.filename: info for info in package.infolist()}
            missing = sorted(selected - info_by_name.keys())
            if missing:
                raise SvtmPackageError(f"selected SVTM ZIP members are missing: {missing[:5]}")
            for name in member_names:
                _safe_member_name(name)
                info = info_by_name[name]
                if info.is_dir() or _is_symlink(info):
                    raise SvtmPackageError(f"selected SVTM member is not a regular file: {name}")
                extracted_bytes += info.file_size
                if extracted_bytes > max_extracted_bytes:
                    raise SvtmPackageError(
                        f"selected SVTM extraction exceeds limit: {extracted_bytes} > {max_extracted_bytes}"
                    )
                if (
                    max_working_set_bytes is not None
                    and archive_bytes + extracted_bytes > max_working_set_bytes
                ):
                    raise SvtmPackageError(
                        "SVTM archive plus selected extraction exceeds working-set limit: "
                        f"{archive_bytes + extracted_bytes} > {max_working_set_bytes}"
                    )
                target = staging.joinpath(*PurePosixPath(name).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with package.open(info) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output, length=1024 * 1024)
        if any(destination.iterdir()):
            raise SvtmPackageError(f"SVTM extraction output became non-empty: {destination}")
        for child in staging.iterdir():
            child.replace(destination / child.name)
        staging.rmdir()
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {
        "output_dir": str(destination),
        "member_count": len(member_names),
        "extracted_bytes": extracted_bytes,
        "member_names": member_names,
    }


def _content_length(headers: Mapping[str, Any]) -> int | None:
    value = headers.get("Content-Length") or headers.get("content-length")
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise SvtmPackageError(f"SVTM package response has invalid Content-Length: {value!r}") from exc
    return parsed if parsed >= 0 else None


def _content_range(headers: Mapping[str, Any]) -> tuple[int, int, int | None] | None:
    value = headers.get("Content-Range") or headers.get("content-range")
    if value is None:
        return None
    match = re.fullmatch(r"bytes\s+(\d+)-(\d+)/(\d+|\*)", str(value).strip())
    if match is None:
        raise SvtmPackageError(f"SVTM package response has invalid Content-Range: {value!r}")
    start, end, total = match.groups()
    return int(start), int(end), None if total == "*" else int(total)


def _save_state(path: Path, *, url: str, part: Path, bytes_written: int, status: str) -> None:
    _write_json(
        path,
        {
            "schema_version": 1,
            "url": url,
            "partial_path": str(part.resolve()),
            "bytes_written": bytes_written,
            "status": status,
        },
    )


def download_svtm_package(
    url: str,
    archive_path: str | Path,
    *,
    max_archive_bytes: int = 4_000_000_000,
    timeout_seconds: float = 60.0,
    max_retries: int = 3,
    backoff_seconds: float = 2.0,
    opener: Callable[..., Any] = urlopen,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Download a ZIP with persistent byte-counted resume state and bounded growth."""

    if max_archive_bytes <= 0 or timeout_seconds <= 0 or max_retries < 0 or backoff_seconds < 0:
        raise ValueError("invalid SVTM package download limits or retry settings")
    destination = Path(archive_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    state_path = destination.with_name(destination.name + ".state.json")
    if destination.is_file():
        if destination.stat().st_size > max_archive_bytes:
            raise SvtmPackageError(f"existing SVTM package exceeds limit: {destination}")
        # A completed archive supersedes any abandoned sibling resume state.
        partial.unlink(missing_ok=True)
        state_path.unlink(missing_ok=True)
        return {
            "archive_path": str(destination),
            "archive_bytes": destination.stat().st_size,
            "reused": True,
            "partial_path": None,
        }

    for attempt in range(max_retries + 1):
        offset = partial.stat().st_size if partial.exists() else 0
        headers = {"User-Agent": "infrastructure-corridor-optimizer/0.1", "Accept": "application/zip"}
        if offset:
            headers["Range"] = f"bytes={offset}-"
        request = Request(url, headers=headers)
        try:
            with opener(request, timeout=timeout_seconds) as response:
                status = getattr(response, "status", None) or response.getcode()
                content_type = str(response.headers.get("Content-Type", "")).lower()
                if status not in (200, 206):
                    raise SvtmPackageError(
                        f"SVTM package endpoint returned HTTP {status}; "
                        "the endpoint may require an interactive web challenge"
                    )
                if offset and status != 206:
                    raise SvtmPackageError(
                        "SVTM package server did not honor Range resume; refusing to duplicate the partial file"
                    )
                if not offset and status != 200:
                    raise SvtmPackageError(
                        "SVTM package server returned a partial response for a new download; "
                        "refusing to create an unverifiable archive"
                    )
                if offset == 0 and "zip" not in content_type and content_type not in ("", "application/octet-stream"):
                    raise SvtmPackageError(
                        f"SVTM package endpoint returned {content_type or 'unknown content'} instead of a ZIP; "
                        "the endpoint may require an interactive web challenge"
                    )
                length = _content_length(response.headers)
                if length is None or length <= 0:
                    raise SvtmPackageError(
                        "SVTM package response has no usable Content-Length; refusing unbounded download"
                    )
                if offset:
                    content_range = _content_range(response.headers)
                    if content_range is None:
                        raise SvtmPackageError(
                            "SVTM package resume response lacks Content-Range; "
                            "refusing to append unverifiable bytes"
                        )
                    range_start, range_end, range_total = content_range
                    if range_start != offset or range_end < range_start:
                        raise SvtmPackageError(
                            "SVTM package resume response has an unexpected byte range; "
                            f"expected start {offset}, observed {range_start}-{range_end}"
                        )
                    if range_end - range_start + 1 != length:
                        raise SvtmPackageError(
                            "SVTM package Content-Range length disagrees with Content-Length"
                        )
                    total = range_total if range_total is not None else offset + length
                    if total != offset + length:
                        raise SvtmPackageError(
                            "SVTM package Content-Range total disagrees with the resumed response"
                        )
                else:
                    total = length
                if total > max_archive_bytes:
                    raise SvtmPackageError(
                        f"SVTM package exceeds max_archive_bytes: {total} > {max_archive_bytes}"
                    )
                mode = "ab" if offset else "wb"
                written = offset
                next_state = written
                with partial.open(mode) as handle:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        written += len(chunk)
                        if written > max_archive_bytes:
                            raise SvtmPackageError(
                                f"SVTM package exceeded max_archive_bytes while streaming: {written}"
                            )
                        handle.write(chunk)
                        if written >= next_state + 8 * 1024 * 1024:
                            _save_state(state_path, url=url, part=partial, bytes_written=written, status="partial")
                            next_state = written
                    handle.flush()
                    os.fsync(handle.fileno())
                if written != total:
                    raise SvtmPackageError(
                        f"SVTM package ended early: expected {total} bytes, observed {written}"
                    )
        except SvtmPackageError:
            _save_state(
                state_path,
                url=url,
                part=partial,
                bytes_written=partial.stat().st_size if partial.exists() else 0,
                status="blocked-or-invalid",
            )
            raise
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            _save_state(
                state_path,
                url=url,
                part=partial,
                bytes_written=partial.stat().st_size if partial.exists() else 0,
                status="retryable-failure",
            )
            if attempt >= max_retries:
                raise SvtmPackageError(f"SVTM package download failed after retries: {url}") from exc
            sleeper(backoff_seconds * (2**attempt))
            continue
        partial.replace(destination)
        state_path.unlink(missing_ok=True)
        return {
            "archive_path": str(destination),
            "archive_bytes": destination.stat().st_size,
            "reused": False,
            "partial_path": None,
        }
    raise SvtmPackageError(f"SVTM package download failed: {url}")
