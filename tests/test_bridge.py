import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch

from PySide6.QtCore import QSettings, QUrl
from PySide6.QtGui import QGuiApplication
from duplicate_cleaner.bridge import AppBridge, MAX_TEXT_PREVIEW_BYTES
from duplicate_cleaner.scanner import scan_for_duplicates

APP = QGuiApplication.instance() or QGuiApplication([])


class BridgeTests(unittest.TestCase):
    def wait_cleanup(self):
        deadline = time.monotonic() + 10
        while self.bridge.get_is_cleaning() and time.monotonic() < deadline:
            APP.processEvents()
            time.sleep(0.005)
        self.assertFalse(self.bridge.get_is_cleaning())
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings = QSettings(str(self.root / "settings.ini"), QSettings.IniFormat)
        with patch("duplicate_cleaner.bridge.QSettings", return_value=self.settings):
            self.bridge = AppBridge()
        self.addCleanup(self.bridge.shutdown)

    def duplicates(self):
        paths = [self.root / "a.txt", self.root / "b.txt"]
        for path in paths:
            path.write_text("same")
        self.bridge._complete_scan(scan_for_duplicates(self.root))
        return paths

    def test_local_url_round_trip(self):
        path = self.root / "space # percent% café.txt"
        url = QUrl.fromLocalFile(str(path)).toString()
        self.assertEqual(self.bridge._normalize_path(url), str(path))
        self.assertEqual(self.bridge.fileUrl(str(path)).toLocalFile(), str(path))

    def test_size_parsing_and_large_qt_property(self):
        self.bridge.setMaxFileSizeText("8 GB")
        self.assertEqual(self.bridge.property("maxFileSizeBytes"), 8 * 1024**3)
        for value in ("nan", "inf", "-1", "bad"):
            self.assertIsNone(self.bridge._parse_size_text(value, default=1))
        self.assertEqual(self.settings.value("maxFileSizeBytes", type=int), 8 * 1024**3)

    def test_preview_is_bounded_and_reuses_scan_hash(self):
        a, _ = self.duplicates()
        self.bridge.selectPreviewFile(str(a))
        self.assertEqual(len(self.bridge.get_preview_data()["fileHash"]), 64)
        a.write_bytes(b"x" * (MAX_TEXT_PREVIEW_BYTES + 50))
        self.bridge.selectPreviewFile(str(a))
        preview = self.bridge.get_preview_data()
        self.assertEqual(len(preview["textContent"]), MAX_TEXT_PREVIEW_BYTES)
        self.assertTrue(preview["isTruncated"])
        self.assertIn("changed", preview["fileHash"])

    def test_trash_success_and_last_copy(self):
        a, b = self.duplicates()
        with patch("duplicate_cleaner.cleanup.QFile") as file:
            file.return_value.moveToTrash.return_value = True
            self.bridge.deleteFile(str(a))
            self.wait_cleanup()
            self.bridge.deleteFile(str(b))
            self.wait_cleanup()
            self.assertEqual(file.return_value.moveToTrash.call_count, 1)
        self.assertEqual(self.bridge.get_deleted_paths(), [str(a)])
        self.assertEqual(self.bridge.get_scan_summary()["wastedBytes"], 0)
        self.assertIn("last copy", self.bridge.get_status_text())

    def test_trash_failure_never_falls_back_to_unlink(self):
        a, _ = self.duplicates()
        with patch("duplicate_cleaner.cleanup.QFile") as file:
            file.return_value.moveToTrash.return_value = False
            file.return_value.errorString.return_value = "Trash unavailable"
            self.bridge.deleteFile(str(a))
            self.wait_cleanup()
        self.assertTrue(a.exists())
        self.assertEqual(self.bridge.get_deleted_paths(), [])
        self.assertIn("Trash unavailable", self.bridge.get_status_text())

    def test_smart_cleanup_keeps_oldest_modified_file(self):
        a, b = self.duplicates()
        os.utime(a, (100, 100))
        os.utime(b, (200, 200))
        self.bridge._complete_scan(scan_for_duplicates(self.root))
        self.assertEqual(self.bridge._collect_magic_cleanup_candidates(), [str(b)])

    def test_portable_folder_open(self):
        a, _ = self.duplicates()
        with patch("duplicate_cleaner.bridge.QDesktopServices.openUrl", return_value=True) as open_url:
            self.bridge.showInFolder(str(a))
            self.assertEqual(open_url.call_args.args[0].toLocalFile(), str(self.root))

    def test_thread_finishes_and_shutdown_cancels(self):
        self.duplicates()
        self.bridge.setSelectedFolder(str(self.root))
        self.bridge.startScan()
        deadline = time.monotonic() + 10
        while self.bridge.get_is_scanning() and time.monotonic() < deadline:
            APP.processEvents()
            time.sleep(0.005)
        self.assertFalse(self.bridge.get_is_scanning())
        self.bridge.startScan()
        self.bridge.shutdown()
        self.assertFalse(self.bridge.get_is_scanning())
