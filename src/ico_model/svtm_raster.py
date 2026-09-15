"""Validate and window-read the official SVTM classified raster representation."""

from __future__ import annotations

import hashlib
import json
import math
import struct
import zipfile
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .svtm_package import SvtmPackageError, validate_svtm_content_report


class SvtmRasterError(RuntimeError):
    """Raised when the SVTM classified raster cannot support the S1 model."""


def _dbf_value(raw: bytes, field_type: str) -> Any:
    value = raw.decode("utf-8", errors="replace").strip()
    if not value:
        return None
    if field_type in {"N", "F"}:
        return float(value) if field_type == "F" or "." in value.lower() or "e" in value.lower() else int(value)
    return value


def read_dbf_from_zip(archive_path: str | Path, member_name: str) -> tuple[list[str], list[dict[str, Any]]]:
    """Read a small dBase value-attribute table directly from the ZIP."""

    try:
        with zipfile.ZipFile(archive_path) as archive:
            raw = archive.read(member_name)
    except (OSError, KeyError, zipfile.BadZipFile) as exc:
        raise SvtmRasterError(f"could not read SVTM value table member: {member_name}") from exc
    if len(raw) < 33:
        raise SvtmRasterError("SVTM value table is truncated")
    record_count, header_length, record_length = struct.unpack_from("<IHH", raw, 4)
    fields: list[tuple[str, str, int]] = []
    offset = 32
    while offset + 32 <= len(raw) and raw[offset] != 0x0D:
        descriptor = raw[offset : offset + 32]
        name = descriptor[:11].split(b"\0", 1)[0].decode("ascii", errors="replace")
        fields.append((name, chr(descriptor[11]), descriptor[16]))
        offset += 32
    if not fields or offset + 1 > header_length:
        raise SvtmRasterError("SVTM value table has no valid field descriptors")
    rows: list[dict[str, Any]] = []
    for index in range(record_count):
        start = header_length + index * record_length
        end = start + record_length
        if end > len(raw):
            raise SvtmRasterError("SVTM value table records are truncated")
        record = raw[start:end]
        if record[:1] == b"*":
            continue
        position = 1
        row: dict[str, Any] = {}
        for name, field_type, width in fields:
            row[name] = _dbf_value(record[position : position + width], field_type)
            position += width
        rows.append(row)
    return [name for name, _field_type, _width in fields], rows


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _zip_member(archive: zipfile.ZipFile, suffix: str) -> zipfile.ZipInfo:
    matches = [info for info in archive.infolist() if info.filename.lower().endswith(suffix.lower())]
    if len(matches) != 1:
        raise SvtmRasterError(f"expected exactly one SVTM {suffix} member, found {len(matches)}")
    return matches[0]


def _validate_metadata_xml(raw: bytes) -> dict[str, Any]:
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise SvtmRasterError("SVTM raster metadata XML is invalid") from exc
    text = " ".join(value.strip() for value in root.itertext() if value.strip())
    if "SVTM_NSW_Extant_PCT_vC2_0_M2_2" not in text:
        raise SvtmRasterError("SVTM raster metadata does not identify release C2.0.M2.2")
    epsg_codes = [
        element.attrib.get("code")
        for element in root.iter()
        if element.tag.rsplit("}", 1)[-1] == "identCode"
    ]
    if "3308" not in epsg_codes:
        raise SvtmRasterError("SVTM raster metadata does not identify EPSG:3308")
    nodata_values = [
        (element.text or "").strip()
        for element in root.iter()
        if element.tag.rsplit("}", 1)[-1] == "NoDataValue"
    ]
    if "65535" not in nodata_values:
        raise SvtmRasterError("SVTM raster metadata does not identify nodata 65535")
    return {
        "release_verified": "C2.0.M2.2",
        "crs_epsg_verified": 3308,
        "nodata_value_verified": 65535,
        "metadata_text_contains_release": True,
    }


def validate_and_materialize_s1_raster(
    archive_path: str | Path,
    output_path: str | Path,
    envelope: Mapping[str, float],
    *,
    target_resolution_m: float = 100.0,
    expected_crs_epsg: int = 3308,
    expected_archive_sha256: str | None = None,
) -> dict[str, Any]:
    """Validate the package raster and write only an S1-resolution window.

    Rasterio is an optional geospatial build dependency. The source TIFF remains
    inside the ZIP and is accessed through GDAL's `/vsizip/` handler; no statewide
    TIFF or geodatabase extraction is performed.
    """

    try:
        import numpy as np
        import rasterio
        from affine import Affine
        from rasterio.enums import Resampling
        from rasterio.transform import array_bounds
        from rasterio.warp import transform_bounds
        from rasterio.windows import Window, from_bounds
    except ImportError as exc:
        raise SvtmRasterError(
            "SVTM raster validation requires the optional geospatial dependencies; "
            "install the project 'geospatial' extra"
        ) from exc

    archive_path = Path(archive_path).resolve()
    output_path = Path(output_path).resolve()
    if not archive_path.is_file():
        raise SvtmRasterError(f"SVTM archive is missing: {archive_path}")
    if target_resolution_m <= 0:
        raise ValueError("target_resolution_m must be positive")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        raise SvtmRasterError(f"SVTM raster output already exists: {output_path}")

    archive_sha256 = expected_archive_sha256 or _sha256(archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        tif_info = _zip_member(archive, ".tif")
        xml_info = _zip_member(archive, ".tif.xml")
        vat_info = _zip_member(archive, ".tif.vat.dbf")
        cpg_info = _zip_member(archive, ".tif.vat.cpg")
        metadata_identity = _validate_metadata_xml(archive.read(xml_info))
        value_table_fields, value_table_rows = read_dbf_from_zip(archive_path, vat_info.filename)
        value_ids = {
            int(row["Value"])
            for row in value_table_rows
            if isinstance(row.get("Value"), (int, float))
        }

    package_root = tif_info.filename.rsplit("/", 1)[0]
    tif_vsi_path = f"/vsizip/{archive_path}/{tif_info.filename}"
    with rasterio.open(tif_vsi_path) as source:
        if source.driver != "GTiff" or source.count != 1 or source.dtypes[0] != "uint16":
            raise SvtmRasterError("SVTM analytical raster is not a single-band uint16 GeoTIFF")
        crs_epsg = source.crs.to_epsg() if source.crs else None
        if crs_epsg != expected_crs_epsg:
            raise SvtmRasterError(
                f"SVTM raster CRS mismatch: expected EPSG:{expected_crs_epsg}, observed EPSG:{crs_epsg}"
            )
        pixel_x, pixel_y = abs(source.transform.a), abs(source.transform.e)
        if abs(pixel_x - 5.0) > 1e-6 or abs(pixel_y - 5.0) > 1e-6:
            raise SvtmRasterError(f"SVTM raster is not 5 m: {pixel_x} x {pixel_y}")
        if source.nodata != 65535:
            raise SvtmRasterError(f"SVTM raster nodata must be 65535, observed {source.nodata}")
        source_bounds = {
            "west": source.bounds.left,
            "south": source.bounds.bottom,
            "east": source.bounds.right,
            "north": source.bounds.top,
        }
        expected_bounds = transform_bounds("EPSG:7844", f"EPSG:{expected_crs_epsg}", *(
            float(envelope[key]) for key in ("west", "south", "east", "north")
        ))
        source_window = from_bounds(*expected_bounds, transform=source.transform)
        col0 = max(0, math.floor(source_window.col_off))
        row0 = max(0, math.floor(source_window.row_off))
        col1 = min(source.width, math.ceil(source_window.col_off + source_window.width))
        row1 = min(source.height, math.ceil(source_window.row_off + source_window.height))
        window = Window(col0, row0, col1 - col0, row1 - row0)
        actual_window_bounds = source.window_bounds(window)
        if (
            actual_window_bounds[0] > expected_bounds[0]
            or actual_window_bounds[1] > expected_bounds[1]
            or actual_window_bounds[2] < expected_bounds[2]
            or actual_window_bounds[3] < expected_bounds[3]
        ):
            raise SvtmRasterError("SVTM source raster window does not cover the S1 envelope")

        source_pixels = int(window.width * window.height)
        output_width = max(1, math.ceil(window.width * pixel_x / target_resolution_m))
        output_height = max(1, math.ceil(window.height * pixel_y / target_resolution_m))
        output = source.read(
            1,
            window=window,
            out_shape=(output_height, output_width),
            resampling=Resampling.nearest,
            masked=False,
        )
        output_transform = source.window_transform(window) * Affine.scale(
            window.width / output_width, window.height / output_height
        )
        output_profile = source.profile.copy()
        output_profile.update(
            driver="GTiff",
            width=output_width,
            height=output_height,
            count=1,
            dtype="uint16",
            crs=source.crs,
            transform=output_transform,
            nodata=65535,
            compress="deflate",
            tiled=True,
            blockxsize=256,
            blockysize=256,
        )
        with rasterio.open(output_path, "w", **output_profile) as destination:
            destination.write(output, 1)
            destination.update_tags(
                source_dataset="NSW State Vegetation Type Map - SVTM (Extant)",
                source_release="C2.0.M2.2",
                source_representation="classified PCT raster",
                source_archive_sha256=archive_sha256,
                processing_scope="configured S1 envelope",
            )

    output_bounds = array_bounds(output_height, output_width, output_transform)
    output_unique = set(int(value) for value in np.unique(output))
    unexpected_output = sorted(output_unique - value_ids - {65535})
    if unexpected_output:
        raise SvtmRasterError(f"S1 raster output has values absent from its VAT: {unexpected_output[:10]}")
    output_nodata_pixels = int((output == 65535).sum())
    output_valid_pixels = int(output.size - output_nodata_pixels)
    report = {
        "representation": "classified-raster",
        "coverage_status": "complete",
        "coverage_scope": "configured-S1-envelope",
        "geometry_type": "classified raster",
        "crs_epsg": expected_crs_epsg,
        "bounds": {
            "west": output_bounds[0],
            "south": output_bounds[1],
            "east": output_bounds[2],
            "north": output_bounds[3],
        },
        "raster_width": output_width,
        "raster_height": output_height,
        "resolution_m": target_resolution_m,
        "nodata_value": 65535,
        "value_table_fields": value_table_fields,
        "value_table_record_count": len(value_table_rows),
        "value_table_value_count": len(value_ids),
        "source_raster_member": tif_info.filename,
        "source_metadata_member": xml_info.filename,
        "source_value_table_member": vat_info.filename,
        "source_code_page_member": cpg_info.filename,
        "source_metadata_identity": metadata_identity,
        "source_raster_bytes_compressed": tif_info.compress_size,
        "source_raster_bytes_uncompressed": tif_info.file_size,
        "source_raster_width": source.width,
        "source_raster_height": source.height,
        "source_raster_resolution_m": pixel_x,
        "source_raster_bounds": source_bounds,
        "source_window": {
            "col_offset": col0,
            "row_offset": row0,
            "width": int(window.width),
            "height": int(window.height),
        },
        "source_value_scan": "nearest-resampled S1 window",
        "source_valid_pixel_count": output_valid_pixels,
        "source_nodata_pixel_count": output_nodata_pixels,
        "source_pixel_count": source_pixels,
        "source_nodata_fraction": output_nodata_pixels / output.size,
        "source_unique_value_count": len(output_unique - {65535}),
        "output_unique_value_count": len(output_unique - {65535}),
        "rest_count_reconciled": "not-applicable-raster-representation",
        "rest_vector_count_reference": 216808,
        "archive_sha256": archive_sha256,
        "archive_path": str(archive_path),
        "package_root": package_root,
    }
    try:
        validate_svtm_content_report(
            report,
            required_fields=("PCTID", "PCTName", "vegClass", "vegForm"),
            expected_crs_epsg=expected_crs_epsg,
        )
    except SvtmPackageError as exc:
        output_path.unlink(missing_ok=True)
        raise SvtmRasterError(str(exc)) from exc
    return report


def write_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    """Write a small provenance report atomically."""

    destination = Path(path)
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(destination)
