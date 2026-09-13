import hashlib
import io
import json
import struct
import tempfile
import unittest
from pathlib import Path
from urllib.error import URLError

from ico_model.dem_acquisition import (
    DemAcquisitionError,
    _download,
    acquire_copernicus_tiles,
    copernicus_tiles,
    inspect_geotiff,
    validate_copernicus_geotiff,
)


def geotiff_fixture() -> bytes:
    entries = []
    entries.extend(
        [
            (256, 4, 1, struct.pack("<I", 3600)),
            (257, 4, 1, struct.pack("<I", 3600)),
            (258, 3, 1, struct.pack("<H", 32) + b"\0\0"),
            (259, 3, 1, struct.pack("<H", 8) + b"\0\0"),
            (277, 3, 1, struct.pack("<H", 1) + b"\0\0"),
            (322, 4, 1, struct.pack("<I", 1024)),
            (323, 4, 1, struct.pack("<I", 1024)),
        ]
    )
    scale_offset = 8 + 2 + 12 * 10 + 4
    tiepoint_offset = scale_offset + 24
    keys_offset = tiepoint_offset + 48
    entries.extend(
        [
            (33550, 12, 3, struct.pack("<I", scale_offset)),
            (33922, 12, 6, struct.pack("<I", tiepoint_offset)),
            (34735, 3, 8, struct.pack("<I", keys_offset)),
        ]
    )
    payload = io.BytesIO()
    payload.write(b"II")
    payload.write(struct.pack("<HIH", 42, 8, len(entries)))
    for tag, type_id, count, value in entries:
        payload.write(struct.pack("<HHI", tag, type_id, count))
        payload.write(value)
    payload.write(struct.pack("<I", 0))
    payload.write(struct.pack("<3d", 1 / 3600, 1 / 3600, 0.0))
    payload.write(struct.pack("<6d", 0, 0, 0, 150, -32, 0))
    payload.write(struct.pack("<8H", 1, 1, 0, 1, 2048, 0, 1, 4326))
    return payload.getvalue()


def xml_fixture() -> bytes:
    return b"""<root><westBoundLongitude>150</westBoundLongitude>
<eastBoundLongitude>151</eastBoundLongitude><southBoundLatitude>-33</southBoundLatitude>
<northBoundLatitude>-32</northBoundLatitude><resolution>1</resolution>
<nrInvalidPixels valueInvalidPixels=\"-32767\">0</nrInvalidPixels></root>"""


class Response:
    def __init__(self, body: bytes, *, etag: str):
        self.body = body
        self.position = 0
        self.headers = {"Content-Length": str(len(body)), "ETag": etag}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, size=-1):
        if size < 0:
            result = self.body[self.position :]
            self.position = len(self.body)
            return result
        result = self.body[self.position : self.position + size]
        self.position += len(result)
        return result


class DemAcquisitionTests(unittest.TestCase):
    def test_tile_selection_covers_each_intersecting_degree(self):
        tiles = copernicus_tiles({"west": 150.82, "south": -33.15, "east": 151.62, "north": -32.27})
        self.assertEqual([tile["tile_id"] for tile in tiles], [
            "Copernicus_DSM_COG_10_S34_00_E150_00_DEM",
            "Copernicus_DSM_COG_10_S34_00_E151_00_DEM",
            "Copernicus_DSM_COG_10_S33_00_E150_00_DEM",
            "Copernicus_DSM_COG_10_S33_00_E151_00_DEM",
        ])
        self.assertTrue(tiles[0]["xml_url"].endswith("Copernicus_DSM_10_S34_00_E150_00.xml"))

    def test_geotiff_validation_checks_crs_resolution_and_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tile.tif"
            path.write_bytes(geotiff_fixture())
            metadata = inspect_geotiff(path)
            validate_copernicus_geotiff(metadata, path)
        self.assertEqual(metadata["bounds"], {"west": 150.0, "south": -33.0, "east": 151.0, "north": -32.0})

    def test_download_retries_transient_get_and_reuses_verified_file(self):
        body = b"dem bytes"
        etag = hashlib.md5(body).hexdigest()
        calls = []
        sleeps = []

        def opener(request, timeout):
            method = request.get_method()
            calls.append(method)
            if method == "GET" and calls.count("GET") == 1:
                raise URLError("temporary")
            return Response(body, etag=etag)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tile.tif"
            result = _download(
                "https://example.test/tile.tif",
                path,
                timeout_seconds=1,
                max_retries=1,
                backoff_seconds=0.25,
                opener=opener,
                sleeper=sleeps.append,
            )
            reused = _download(
                "https://example.test/tile.tif",
                path,
                timeout_seconds=1,
                max_retries=0,
                backoff_seconds=0,
                opener=opener,
                sleeper=sleeps.append,
            )
        self.assertFalse(result["reused"])
        self.assertTrue(reused["reused"])
        self.assertEqual(sleeps, [0.25])

    def test_acquisition_publishes_manifest_only_after_tile_validation(self):
        tif = geotiff_fixture()
        xml = xml_fixture()
        objects = {}
        for suffix, body in ((".tif", tif), (".xml", xml)):
            objects[suffix] = body

        def opener(request, timeout):
            body = objects[Path(request.full_url).suffix]
            return Response(body, etag=hashlib.md5(body).hexdigest())

        with tempfile.TemporaryDirectory() as directory:
            manifest_path = acquire_copernicus_tiles(
                {"west": 150.2, "south": -32.8, "east": 150.7, "north": -32.2},
                directory,
                source_id="copernicus-dem-glo-30",
                timeout_seconds=1,
                max_retries=0,
                opener=opener,
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["tile_count"], 1)
        self.assertEqual(manifest["coverage_status"], "complete")

    def test_acquisition_rejects_bad_tile_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.tif"
            path.write_bytes(b"not a tiff")
            with self.assertRaises(DemAcquisitionError):
                inspect_geotiff(path)

    def test_acquisition_rejects_tile_set_before_download_limit_is_exceeded(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(DemAcquisitionError, "max_tiles"):
                acquire_copernicus_tiles(
                    {"west": 150, "south": -34, "east": 152, "north": -32},
                    directory,
                    max_tiles=1,
                )


if __name__ == "__main__":
    unittest.main()
