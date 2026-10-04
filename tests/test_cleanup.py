from pathlib import Path
import os
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from duplicate_cleaner.cleanup import CleanupWorker
from duplicate_cleaner.scanner import scan_for_duplicates


class CleanupTests(unittest.TestCase):
    @unittest.skipUnless(
        os.name == "nt" and os.environ.get("DUPLICATE_CLEANER_TEST_TRASH") == "1",
        "Opt-in native Windows Recycle Bin integration",
    )
    def test_native_recycle_bin_preserves_last_copy(self):
        with TemporaryDirectory(prefix="duplicate-cleaner-trash-test-") as tmp:
            paths = [Path(tmp) / name for name in ("discard.txt", "retain.txt")]
            for path in paths:
                path.write_text("Disposable Duplicate Cleaner integration test fixture.")
            groups = scan_for_duplicates(Path(tmp))["groups"]
            worker = CleanupWorker([str(path) for path in paths], groups, [])
            results = []
            worker.finished.connect(results.append)
            worker.run()
            self.assertEqual(results[0]["removed"], 1, results)
            self.assertFalse(paths[0].exists())
            self.assertTrue(paths[1].exists())
            self.assertIn("last copy", results[0]["errors"][0])

    def test_cancellation_during_verification_does_not_trash(self):
        with TemporaryDirectory() as tmp:
            paths = [Path(tmp) / name for name in ("a", "b")]
            for path in paths:
                path.write_bytes(b"same")
            groups = scan_for_duplicates(Path(tmp))["groups"]
            worker = CleanupWorker([str(paths[0])], groups, [])
            results = []
            worker.finished.connect(results.append)
            from duplicate_cleaner.safety import validate_removal
            def cancel(*args):
                worker.cancel()
                validate_removal(*args)
            with patch("duplicate_cleaner.cleanup.validate_removal", side_effect=cancel), patch("duplicate_cleaner.cleanup.QFile") as file:
                worker.run()
                file.assert_not_called()
            self.assertTrue(results[0]["cancelled"])
            self.assertEqual(results[0]["removed"], 0)

    def test_unknown_path_is_refused(self):
        worker = CleanupWorker(["unscanned.txt"], [], [])
        results = []
        worker.finished.connect(results.append)
        with patch("duplicate_cleaner.cleanup.QFile") as file:
            worker.run()
            file.assert_not_called()
        self.assertIn("not in the current scan", results[0]["errors"][0])
