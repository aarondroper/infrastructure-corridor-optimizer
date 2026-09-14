import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from urllib.error import URLError

from ico_model.svtm_package import (
    SvtmPackageError,
    download_svtm_package,
    inspect_svtm_zip,
    extract_svtm_members,
    validate_svtm_content_report,
)
from ico_model.svtm_raster import _validate_metadata_xml


class FakeResponse:
    def __init__(self, payload=b"", *, status=200, headers=None):
        self._stream = io.BytesIO(payload)
        self.status = status
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def getcode(self):
        return self.status

    def read(self, size=-1):
        return self._stream.read(size)


class SvtmPackageTests(unittest.TestCase):
    def test_zip_inspection_identifies_vector_candidate_and_crc(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "package.zip"
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr("SVTM/extent.shp", b"shape")
                package.writestr("SVTM/extent.dbf", b"attributes")
                package.writestr("SVTM/readme.pdf", b"documentation")
            report = inspect_svtm_zip(archive)
            self.assertTrue(report["vector_candidate_present"])
            self.assertEqual(report["member_count"], 3)

    def test_zip_inspection_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "package.zip"
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr("../outside.shp", b"shape")
            with self.assertRaisesRegex(SvtmPackageError, "unsafe path"):
                inspect_svtm_zip(archive)

    def test_zip_inspection_does_not_treat_unrelated_json_as_vector(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "package.zip"
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr("metadata/config.json", b"{}")
            report = inspect_svtm_zip(archive)
            self.assertFalse(report["vector_candidate_present"])

    def test_download_resumes_partial_file_without_duplicate_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "package.zip"
            partial = archive.with_name("package.zip.part")
            partial.write_bytes(b"abc")

            def opener(request, timeout):
                self.assertEqual(request.headers["Range"], "bytes=3-")
                return FakeResponse(
                    b"def",
                    status=206,
                    headers={
                        "Content-Type": "application/zip",
                        "Content-Length": "3",
                        "Content-Range": "bytes 3-5/6",
                    },
                )

            result = download_svtm_package("https://example.test/package.zip", archive, opener=opener)
            self.assertFalse(result["reused"])
            self.assertEqual(archive.read_bytes(), b"abcdef")
            self.assertFalse(partial.exists())

    def test_download_records_waf_block_without_writing_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "package.zip"

            def opener(_request, timeout):
                return FakeResponse(b"challenge", status=202, headers={"Content-Type": "text/html"})

            with self.assertRaisesRegex(SvtmPackageError, "interactive web challenge"):
                download_svtm_package("https://example.test/package.zip", archive, opener=opener)
            self.assertFalse(archive.exists())
            state = json.loads(archive.with_name("package.zip.state.json").read_text())
            self.assertEqual(state["status"], "blocked-or-invalid")

    def test_download_rejects_mismatched_resume_range_without_appending(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "package.zip"
            partial = archive.with_name("package.zip.part")
            partial.write_bytes(b"abc")

            def opener(request, timeout):
                return FakeResponse(
                    b"def",
                    status=206,
                    headers={
                        "Content-Type": "application/zip",
                        "Content-Length": "3",
                        "Content-Range": "bytes 0-2/6",
                    },
                )

            with self.assertRaisesRegex(SvtmPackageError, "unexpected byte range"):
                download_svtm_package("https://example.test/package.zip", archive, opener=opener)
            self.assertEqual(partial.read_bytes(), b"abc")
            self.assertFalse(archive.exists())

    def test_download_retries_retryable_failure_and_finishes_once(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "package.zip"
            calls = []
            delays = []

            def opener(request, timeout):
                calls.append(request.headers.get("Range"))
                if len(calls) == 1:
                    raise URLError("temporary failure")
                return FakeResponse(
                    b"abcdef",
                    status=200,
                    headers={"Content-Type": "application/zip", "Content-Length": "6"},
                )

            result = download_svtm_package(
                "https://example.test/package.zip",
                archive,
                max_retries=1,
                backoff_seconds=0.25,
                opener=opener,
                sleeper=delays.append,
            )
            self.assertFalse(result["reused"])
            self.assertEqual(archive.read_bytes(), b"abcdef")
            self.assertEqual(calls, [None, None])
            self.assertEqual(delays, [0.25])

    def test_content_report_requires_model_fields_coverage_and_rest_count(self):
        report = validate_svtm_content_report(
            {
                "coverage_status": "complete",
                "coverage_scope": "configured-S1-envelope",
                "geometry_type": "esriGeometryPolygon",
                "crs_epsg": 3308,
                "feature_count": 216808,
                "unique_id_count": 216808,
                "duplicate_id_count": 0,
                "rest_count_reconciled": True,
                "fields": ["OBJECTID", "PCTID", "PCTName", "vegClass", "vegForm"],
                "bounds": {"west": 140, "south": -38, "east": 154, "north": -28},
            },
            required_fields=("OBJECTID", "PCTID", "PCTName", "vegClass", "vegForm"),
            expected_bounds={"west": 150.82, "south": -33.15, "east": 151.62, "north": -32.27},
        )
        self.assertEqual(report["feature_count"], 216808)

    def test_classified_raster_report_validates_without_vector_count(self):
        report = validate_svtm_content_report(
            {
                "representation": "classified-raster",
                "coverage_status": "complete",
                "coverage_scope": "configured-S1-envelope",
                "geometry_type": "classified raster",
                "crs_epsg": 3308,
                "raster_width": 788,
                "raster_height": 1004,
                "resolution_m": 100,
                "nodata_value": 65535,
                "value_table_fields": ["Value", "PCTID", "PCTName", "vegClass", "vegForm"],
                "rest_count_reconciled": "not-applicable-raster-representation",
                "bounds": {"west": 9655964, "south": 4501550, "east": 9734785, "north": 4602015},
            },
            required_fields=("PCTID", "PCTName", "vegClass", "vegForm"),
            expected_bounds={"west": 9655969, "south": 4501558, "east": 9734784, "north": 4602009},
        )
        self.assertEqual(report["representation"], "classified-raster")
        self.assertIsNone(report["feature_count"])

    def test_raster_metadata_xml_identifies_release_crs_and_nodata(self):
        metadata = _validate_metadata_xml(
            b"<metadata><itemName>SVTM_NSW_Extant_PCT_vC2_0_M2_2_5m</itemName>"
            b"<identCode code='3308'/><NoDataValue>65535</NoDataValue></metadata>"
        )
        self.assertEqual(metadata["release_verified"], "C2.0.M2.2")

    def test_extraction_requires_explicit_members_and_is_atomic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "package.zip"
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr("SVTM/extent.shp", b"shape")
                package.writestr("SVTM/extent.dbf", b"attributes")
            output = root / "selected"
            result = extract_svtm_members(archive, output, ["SVTM/extent.shp"], allow_temporary=True)
            self.assertEqual(result["extracted_bytes"], 5)
            self.assertEqual((output / "SVTM/extent.shp").read_bytes(), b"shape")

    def test_extraction_enforces_archive_plus_selected_working_set(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "package.zip"
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr("SVTM/extent.shp", b"shape")
            with self.assertRaisesRegex(SvtmPackageError, "working-set limit"):
                extract_svtm_members(
                    archive,
                    root / "selected",
                    ["SVTM/extent.shp"],
                    max_working_set_bytes=archive.stat().st_size + 4,
                    allow_temporary=True,
                )


if __name__ == "__main__":
    unittest.main()
