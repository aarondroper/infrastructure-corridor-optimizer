import tempfile
import unittest
from pathlib import Path

from scripts.cleanup_acquisition_storage import _explicit_candidate, _safe_root


class AcquisitionCleanupTests(unittest.TestCase):
    def test_explicit_candidate_targets_only_the_named_namespace(self):
        with tempfile.TemporaryDirectory() as directory:
            namespace = Path(directory) / "source--component--page-250"
            namespace.mkdir()
            self.assertEqual(_explicit_candidate(namespace, 0), [namespace])

    def test_cleanup_rejects_system_temporary_roots(self):
        with self.assertRaises(ValueError):
            _safe_root(Path(tempfile.gettempdir()))


if __name__ == "__main__":
    unittest.main()
