"""Credential-free Copernicus GLO-30 tile acquisition and metadata checks."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import struct
import tempfile
import time
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .sources import write_manifest


COPERNICUS_DEM_BUCKET = "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com"


class DemAcquisitionError(ValueError):
    """Raised when public DEM acquisition or tile validation fails."""


def _tile_stem(latitude: int, longitude: int) -> str:
    if latitude < 0:
        latitude_part = f"S{abs(latitude):02d}"
    else:
        latitude_part = f"N{latitude:02d}"
    if longitude < 0:
        longitude_part = f"W{abs(longitude):03d}"
    else:
        longitude_part = f"E{longitude:03d}"
    return f"Copernicus_DSM_COG_10_{latitude_part}_00_{longitude_part}_00_DEM"


def copernicus_tiles(envelope: Mapping[str, float]) -> list[dict[str, Any]]:
    """Return the 1° public GLO-30 tiles intersecting a lon/lat envelope."""

    west, south, east, north = (
        float(envelope["west"]),
        float(envelope["south"]),
        float(envelope["east"]),
        float(envelope["north"]),
    )
    if not (west < east and south < north):
        raise DemAcquisitionError("DEM envelope must have positive dimensions")
    tiles: list[dict[str, Any]] = []
    for latitude in range(math.floor(south), math.ceil(north)):
        for longitude in range(math.floor(west), math.ceil(east)):
            stem = _tile_stem(latitude, longitude)
            tiles.append(
                {
                    "tile_id": f"{stem}",
                    "stem": stem,
                    "west": float(longitude),
                    "south": float(latitude),
                    "east": float(longitude + 1),
            "north": float(latitude + 1),
            "url": f"{COPERNICUS_DEM_BUCKET}/{stem}/{stem}.tif",
            "xml_url": (
                f"{COPERNICUS_DEM_BUCKET}/{stem}/"
                f"{stem.replace('_COG_10', '_10').removesuffix('_DEM')}.xml"
            ),
                }
            )
    return tiles


_TIFF_TYPES: dict[int, tuple[str, int]] = {
    1: ("B", 1),
    2: ("s", 1),
    3: ("H", 2),
    4: ("I", 4),
    5: ("II", 8),
    12: ("d", 8),
}


def _read_tiff_values(handle: Any, endian: str, type_id: int, count: int, inline: bytes) -> Any:
    type_info = _TIFF_TYPES.get(type_id)
    if type_info is None:
        raise DemAcquisitionError(f"unsupported GeoTIFF field type: {type_id}")
    fmt, size = type_info
    total = size * count
    raw = inline[:total] if total <= 4 else None
    if raw is None:
        offset = struct.unpack(endian + "I", inline)[0]
        current_position = handle.tell()
        handle.seek(offset)
        raw = handle.read(total)
        handle.seek(current_position)
    if len(raw) != total:
        raise DemAcquisitionError("GeoTIFF tag value is truncated")
    if type_id == 2:
        return raw.rstrip(b"\0").decode("ascii", errors="replace")
    values = struct.unpack(endian + fmt * count, raw)
    return values[0] if count == 1 else values


def inspect_geotiff(path: str | Path) -> dict[str, Any]:
    """Inspect the structural GeoTIFF tags needed for DEM suitability."""

    path = Path(path)
    try:
        handle = path.open("rb")
    except OSError as exc:
        raise DemAcquisitionError(f"could not open DEM GeoTIFF: {path}") from exc
    with handle:
        header = handle.read(8)
        if len(header) != 8 or header[:2] not in (b"II", b"MM"):
            raise DemAcquisitionError(f"DEM is not a TIFF: {path}")
        endian = "<" if header[:2] == b"II" else ">"
        magic, ifd_offset = struct.unpack(endian + "HI", header[2:])
        if magic != 42:
            raise DemAcquisitionError(f"unsupported non-classic TIFF: {path}")
        handle.seek(ifd_offset)
        count_raw = handle.read(2)
        if len(count_raw) != 2:
            raise DemAcquisitionError(f"GeoTIFF has no image directory: {path}")
        count = struct.unpack(endian + "H", count_raw)[0]
        tags: dict[int, Any] = {}
        for _ in range(count):
            entry = handle.read(12)
            if len(entry) != 12:
                raise DemAcquisitionError(f"GeoTIFF image directory is truncated: {path}")
            tag, type_id, value_count = struct.unpack(endian + "HHI", entry[:8])
            try:
                tags[tag] = _read_tiff_values(handle, endian, type_id, value_count, entry[8:])
            except (struct.error, UnicodeError) as exc:
                raise DemAcquisitionError(f"GeoTIFF tag {tag} is invalid: {path}") from exc

    required = {256: "width", 257: "height", 258: "bits_per_sample", 259: "compression", 277: "samples_per_pixel", 322: "tile_width", 323: "tile_height", 33550: "pixel_scale", 33922: "tiepoint", 34735: "geo_keys"}
    missing = [name for tag, name in required.items() if tag not in tags]
    if missing:
        raise DemAcquisitionError(f"DEM GeoTIFF is missing tags {missing}: {path}")
    width = int(tags[256])
    height = int(tags[257])
    scale = tags[33550]
    tiepoint = tags[33922]
    if width <= 0 or height <= 0 or not isinstance(scale, tuple) or len(scale) < 2 or not isinstance(tiepoint, tuple) or len(tiepoint) < 6:
        raise DemAcquisitionError(f"DEM GeoTIFF has invalid dimensions/georeferencing: {path}")
    pixel_x, pixel_y = float(scale[0]), float(scale[1])
    west, north = float(tiepoint[3]), float(tiepoint[4])
    bounds = {
        "west": west,
        "south": north - height * pixel_y,
        "east": west + width * pixel_x,
        "north": north,
    }
    geo_keys = tags[34735]
    if not isinstance(geo_keys, tuple) or len(geo_keys) < 4:
        raise DemAcquisitionError(f"DEM GeoTIFF has invalid GeoKeyDirectory: {path}")
    crs_epsg = None
    for offset in range(4, len(geo_keys), 4):
        key, location, value_count, value_offset = geo_keys[offset : offset + 4]
        if key == 2048 and location == 0 and value_count == 1:
            crs_epsg = int(value_offset)
    if crs_epsg is None:
        raise DemAcquisitionError(f"DEM GeoTIFF does not declare a geographic CRS: {path}")
    if crs_epsg != 4326:
        raise DemAcquisitionError(f"DEM GeoTIFF CRS must be EPSG:4326, observed {crs_epsg}: {path}")
    nodata = tags.get(42113)
    try:
        nodata_value = float(nodata) if nodata is not None else None
    except (TypeError, ValueError) as exc:
        raise DemAcquisitionError(f"DEM GeoTIFF nodata tag is invalid: {path}") from exc
    return {
        "path": str(path),
        "width": width,
        "height": height,
        "bits_per_sample": int(tags[258]),
        "compression": int(tags[259]),
        "samples_per_pixel": int(tags[277]),
        "tiled": 322 in tags and 323 in tags,
        "tile_width": int(tags[322]),
        "tile_height": int(tags[323]),
        "pixel_scale_degrees": [pixel_x, pixel_y],
        "nominal_resolution_m": 30.0,
        "crs_epsg": crs_epsg,
        "bounds": bounds,
        "nodata_value": nodata_value,
    }


def validate_copernicus_geotiff(metadata: Mapping[str, Any], path: str | Path) -> None:
    """Enforce the structural properties required from a GLO-30 source tile."""

    if metadata.get("crs_epsg") != 4326:
        raise DemAcquisitionError(f"DEM tile CRS must be EPSG:4326: {path}")
    if metadata.get("width") != 3600 or metadata.get("height") != 3600:
        raise DemAcquisitionError(f"DEM tile dimensions are not 1-degree GLO-30: {path}")
    if metadata.get("bits_per_sample") != 32 or metadata.get("samples_per_pixel") != 1:
        raise DemAcquisitionError(f"DEM tile must be single-band 32-bit: {path}")
    if metadata.get("tiled") is not True:
        raise DemAcquisitionError(f"DEM tile must be tiled: {path}")
    expected_scale = 1 / 3600
    scale = metadata.get("pixel_scale_degrees")
    if (
        not isinstance(scale, list)
        or len(scale) < 2
        or abs(float(scale[0]) - expected_scale) > 1e-12
        or abs(float(scale[1]) - expected_scale) > 1e-12
    ):
        raise DemAcquisitionError(f"DEM tile resolution is not one arc-second: {path}")


def _retryable(code: int) -> bool:
    return code in {408, 425, 429, 500, 502, 503, 504}


def _download(
    url: str,
    destination: Path,
    *,
    timeout_seconds: float,
    max_retries: int,
    backoff_seconds: float,
    opener: Callable[..., Any],
    sleeper: Callable[[float], None],
) -> dict[str, Any]:
    """Download one object atomically, reusing a verified local object."""

    for attempt in range(max_retries + 1):
        try:
            with opener(Request(url, method="HEAD"), timeout=timeout_seconds) as response:
                expected_size = int(response.headers.get("Content-Length", "0"))
                etag = response.headers.get("ETag", "").strip('"')
            break
        except HTTPError as exc:
            if _retryable(exc.code) and attempt < max_retries:
                sleeper(backoff_seconds * (2**attempt))
                continue
            raise DemAcquisitionError(f"DEM HEAD request failed ({exc.code}): {url}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            if attempt < max_retries:
                sleeper(backoff_seconds * (2**attempt))
                continue
            raise DemAcquisitionError(f"DEM HEAD request failed: {url}") from exc
    if expected_size <= 0:
        raise DemAcquisitionError(f"DEM object has no positive Content-Length: {url}")

    def digest(path: Path) -> tuple[int, str, str]:
        sha256 = hashlib.sha256()
        md5 = hashlib.md5()
        size = 0
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                size += len(chunk)
                sha256.update(chunk)
                md5.update(chunk)
        return size, sha256.hexdigest(), md5.hexdigest()

    if destination.is_file():
        size, sha256, md5 = digest(destination)
        if size == expected_size and (not etag or "-" in etag or md5 == etag):
            return {"size": size, "sha256": sha256, "etag": etag, "reused": True}

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_fd, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(temporary_fd)
    temporary = Path(temporary_name)
    try:
        for attempt in range(max_retries + 1):
            try:
                with opener(Request(url), timeout=timeout_seconds) as response, temporary.open("wb") as handle:
                    shutil.copyfileobj(response, handle, length=1024 * 1024)
                size, sha256, md5 = digest(temporary)
                if size != expected_size or (etag and "-" not in etag and md5 != etag):
                    raise DemAcquisitionError(f"DEM object size/checksum mismatch: {url}")
                temporary.replace(destination)
                return {"size": size, "sha256": sha256, "etag": etag, "reused": False}
            except HTTPError as exc:
                if _retryable(exc.code) and attempt < max_retries:
                    sleeper(backoff_seconds * (2**attempt))
                    continue
                raise DemAcquisitionError(f"DEM download failed ({exc.code}): {url}") from exc
            except (URLError, TimeoutError, OSError) as exc:
                if attempt < max_retries:
                    sleeper(backoff_seconds * (2**attempt))
                    continue
                raise DemAcquisitionError(f"DEM download failed: {url}") from exc
    finally:
        temporary.unlink(missing_ok=True)
    raise DemAcquisitionError(f"DEM download failed after retries: {url}")


def _xml_metadata(path: Path) -> dict[str, Any]:
    try:
        root = ET.fromstring(path.read_bytes())
    except (OSError, ET.ParseError) as exc:
        raise DemAcquisitionError(f"Copernicus tile XML is unreadable: {path}") from exc
    values = {
        element.tag.rsplit("}", 1)[-1]: element
        for element in root.iter()
        if element.tag.rsplit("}", 1)[-1]
        in {"westBoundLongitude", "eastBoundLongitude", "southBoundLatitude", "northBoundLatitude", "resolution", "nrInvalidPixels"}
    }
    def text(name: str) -> float:
        element = values.get(name)
        try:
            raw_text = (element.text or "").strip()
            if not raw_text:
                raw_text = next(
                    child.text.strip()
                    for child in element.iter()
                    if child is not element and child.text and child.text.strip()
                )
            return float(raw_text)
        except (AttributeError, TypeError, ValueError) as exc:
            raise DemAcquisitionError(f"Copernicus XML has no numeric {name}: {path}") from exc
    invalid = values.get("nrInvalidPixels")
    invalid_value = invalid.attrib.get("valueInvalidPixels") if invalid is not None else None
    if invalid_value is None:
        raise DemAcquisitionError(f"Copernicus XML has no invalid-pixel value: {path}")
    return {
        "bounds": {"west": text("westBoundLongitude"), "east": text("eastBoundLongitude"), "south": text("southBoundLatitude"), "north": text("northBoundLatitude")},
        "invalid_pixel_value": float(invalid_value),
        "invalid_pixel_count": int(float(invalid.text or "0")),
    }


def acquire_copernicus_tiles(
    envelope: Mapping[str, float],
    output_dir: str | Path,
    *,
    source_id: str = "copernicus-dem-glo-30",
    timeout_seconds: float = 60.0,
    max_retries: int = 3,
    backoff_seconds: float = 1.0,
    max_tiles: int = 16,
    max_total_bytes: int = 300_000_000,
    opener: Callable[..., Any] = urlopen,
    sleeper: Callable[[float], None] = time.sleep,
) -> Path:
    """Acquire, inspect, and publish a complete external Copernicus tile set."""

    if timeout_seconds <= 0 or not math.isfinite(timeout_seconds):
        raise DemAcquisitionError("timeout_seconds must be finite and positive")
    if max_retries < 0 or not isinstance(max_retries, int):
        raise DemAcquisitionError("max_retries must be a non-negative integer")
    if backoff_seconds < 0 or not math.isfinite(backoff_seconds):
        raise DemAcquisitionError("backoff_seconds must be finite and non-negative")
    if isinstance(max_tiles, bool) or not isinstance(max_tiles, int) or max_tiles <= 0:
        raise DemAcquisitionError("max_tiles must be a positive integer")
    if isinstance(max_total_bytes, bool) or not isinstance(max_total_bytes, int) or max_total_bytes <= 0:
        raise DemAcquisitionError("max_total_bytes must be a positive integer")
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    tiles = copernicus_tiles(envelope)
    if len(tiles) > max_tiles:
        raise DemAcquisitionError(
            f"DEM tile set exceeds max_tiles: {len(tiles)} > {max_tiles}"
        )
    records: list[dict[str, Any]] = []
    for tile in tiles:
        tile_path = destination / "tiles" / f"{tile['stem']}.tif"
        xml_path = destination / "tiles" / f"{tile['stem']}.xml"
        checksum = _download(tile["url"], tile_path, timeout_seconds=timeout_seconds, max_retries=max_retries, backoff_seconds=backoff_seconds, opener=opener, sleeper=sleeper)
        _download(tile["xml_url"], xml_path, timeout_seconds=timeout_seconds, max_retries=max_retries, backoff_seconds=backoff_seconds, opener=opener, sleeper=sleeper)
        geotiff = inspect_geotiff(tile_path)
        validate_copernicus_geotiff(geotiff, tile_path)
        xml = _xml_metadata(xml_path)
        if any(
            abs(geotiff["bounds"][key] - xml["bounds"][key]) > 0.001
            for key in ("west", "south", "east", "north")
        ):
            raise DemAcquisitionError(f"GeoTIFF/XML bounds mismatch: {tile['tile_id']}")
        if xml["invalid_pixel_value"] != -32767:
            raise DemAcquisitionError(f"unexpected Copernicus nodata value: {tile['tile_id']}")
        total_bytes = sum(record["download"]["size"] for record in records) + checksum["size"]
        if total_bytes > max_total_bytes:
            raise DemAcquisitionError(
                f"DEM tile set exceeds max_total_bytes: {total_bytes} > {max_total_bytes}"
            )
        records.append(
            {
                "tile_id": tile["tile_id"],
                "url": tile["url"],
                "xml_url": tile["xml_url"],
                "artifact_path": str(tile_path.relative_to(destination)),
                "xml_path": str(xml_path.relative_to(destination)),
                "bounds": {
                    key: tile[key] for key in ("west", "south", "east", "north")
                },
                "download": checksum,
                "geotiff": geotiff,
                "xml_metadata": xml,
            }
        )
    bounds = {
        "west": min(record["bounds"]["west"] for record in records),
        "south": min(record["bounds"]["south"] for record in records),
        "east": max(record["bounds"]["east"] for record in records),
        "north": max(record["bounds"]["north"] for record in records),
    }
    manifest = {
        "schema_version": 1,
        "format": "copernicus-dem-tile-set",
        "source_id": source_id,
        "source_url": COPERNICUS_DEM_BUCKET,
        "artifact_type": "raster-dem-tile-set",
        "artifact_path": "dem_manifest.json",
        "bounds": bounds,
        "bounds_crs_epsg": 4326,
        "crs_epsg": 4326,
        "resolution_m": 30.0,
        "pixel_scale_degrees": [1 / 3600, 1 / 3600],
        "nodata_defined": True,
        "nodata_value": -32767,
        "coverage_status": "complete",
        "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
        "tile_count": len(records),
        "tiles": records,
        "requested_envelope": dict(envelope),
        "storage": {
            "tile_bytes": sum(record["download"]["size"] for record in records),
            "tile_count": len(records),
            "max_total_bytes": max_total_bytes,
        },
    }
    manifest_path = destination / "dem_manifest.json"
    write_manifest(manifest, manifest_path)
    return manifest_path
