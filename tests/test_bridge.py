import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
import time
import unittest
from unittest.mock import patch

from PySide6.QtCore import QSettings, QSize, QUrl
from PySide6.QtGui import QColor, QGuiApplication, QImage, QImageReader, QPainter, QPdfWriter
from PySide6.QtPdf import QPdfDocument
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
    def wait_scan(self):
        deadline = time.monotonic() + 10
        while self.bridge.get_is_scanning() and time.monotonic() < deadline:
            APP.processEvents()
            time.sleep(0.005)
        self.assertFalse(self.bridge.get_is_scanning())

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

    @unittest.skipUnless(os.name == "nt", "Native Windows path semantics")
    def test_windows_drive_and_unc_url_round_trip(self):
        for value in (r"C:\Users\Example\space # percent% café.txt", r"\\server\share\space # café.txt"):
            with self.subTest(path=value):
                expected = os.path.normcase(os.path.normpath(value))
                url = QUrl.fromLocalFile(value).toString()
                normalized = self.bridge._normalize_path(url)
                self.assertEqual(os.path.normcase(normalized), expected)
                self.assertEqual(os.path.normcase(os.path.normpath(
                    self.bridge.fileUrl(value).toLocalFile()
                )), expected)

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

    def test_image_preview_url_can_be_decoded(self):
        path = self.root / "image # café.png"
        image = QImage(16, 16, QImage.Format.Format_RGB32)
        image.fill(QColor("red"))
        self.assertTrue(image.save(str(path)))
        self.bridge.selectPreviewFile(str(path))
        preview = self.bridge.get_preview_data()
        self.assertEqual(preview["previewKind"], "image")
        reader = QImageReader(QUrl(preview["previewUrl"]).toLocalFile())
        self.assertEqual(reader.read().size(), QSize(16, 16))

    def test_pdf_preview_url_can_be_rendered(self):
        path = self.root / "document # café.pdf"
        writer = QPdfWriter(str(path))
        painter = QPainter(writer)
        painter.fillRect(0, 0, 100, 100, QColor("blue"))
        painter.end()
        del writer
        self.bridge.selectPreviewFile(str(path))
        preview = self.bridge.get_preview_data()
        self.assertEqual(preview["previewKind"], "pdf")
        document = QPdfDocument()
        try:
            document.load(QUrl(preview["previewUrl"]).toLocalFile())
            self.assertEqual(document.pageCount(), 1)
            self.assertFalse(document.render(0, QSize(128, 128)).isNull())
        finally:
            document.close()

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

    def test_scan_respects_saved_extension_and_folder_filters(self):
        for name in ("keep/alpha.txt", "keep/beta.TXT", "skip/alpha.txt", "skip/beta.txt"):
            path = self.root / name
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(b"same")
        self.bridge.setUseOnlySearchFileExtension(True)
        self.bridge.setOnlySearchFileExtensionText("TXT")
        self.bridge.setUseIgnoreFolderPatterns(True)
        self.bridge.addIgnoreFolderPattern(r"/skip/")
        self.bridge.setSelectedFolder(str(self.root))
        self.bridge.startScan()
        self.wait_scan()
        groups = self.bridge.get_duplicate_groups()
        self.assertEqual(len(groups), 1)
        self.assertEqual(set(groups[0]["files"]), {
            str(self.root / "keep/alpha.txt"), str(self.root / "keep/beta.TXT")
        })
        self.assertEqual(self.bridge.get_scan_summary()["phase"], "Complete")
        self.assertEqual(self.bridge.get_only_search_file_extension(), ".txt")
        self.assertEqual(self.settings.value("onlySearchFileExtension"), ".txt")
        self.assertEqual(self.settings.value("ignoreFolderPatterns"), [r"/skip/"])

    def test_switching_folder_clears_results_preview_and_deleted_paths(self):
        a, _ = self.duplicates()
        self.bridge.selectPreviewFile(str(a))
        self.bridge._record_removed(str(a))
        other = self.root / "other"
        other.mkdir()
        self.bridge.setSelectedFolder(str(other))
        self.assertEqual(self.bridge.get_duplicate_groups(), [])
        self.assertEqual(self.bridge.get_deleted_paths(), [])
        self.assertEqual(self.bridge.get_preview_data()["path"], "")
        self.assertEqual(self.bridge.get_scan_summary()["phase"], "Ready")
        self.assertEqual(self.bridge.get_magic_cleanup_candidate_count(), 0)

    def test_scan_preferences_survive_bridge_restart(self):
        self.bridge.setSelectedFolder(str(self.root))
        self.bridge.startScan()
        self.wait_scan()
        self.bridge.setIgnoreEmptyFiles(False)
        self.bridge.setIncludeSubfolders(False)
        self.bridge.setUseDuplicateSearchLimit(False)
        self.bridge.setDuplicateSearchLimitText("27")
        self.bridge.addIgnoreFileExtension("TXT")
        self.bridge.setUseIgnoreFileExtensions(True)
        self.bridge.setOnlySearchFileExtensionText("bin")
        self.settings.sync()

        settings = QSettings(str(self.root / "settings.ini"), QSettings.IniFormat)
        with patch("duplicate_cleaner.bridge.QSettings", return_value=settings):
            reloaded = AppBridge()
        self.addCleanup(reloaded.shutdown)
        self.assertFalse(reloaded.get_ignore_empty_files())
        self.assertFalse(reloaded.get_include_subfolders())
        self.assertFalse(reloaded.get_use_duplicate_search_limit())
        self.assertEqual(reloaded.get_duplicate_search_limit(), 27)
        self.assertEqual(reloaded.get_ignore_file_extensions(), [".txt"])
        self.assertTrue(reloaded.get_use_ignore_file_extensions())
        self.assertEqual(reloaded.get_only_search_file_extension(), ".bin")
        self.assertEqual(reloaded.get_recent_folders()[0], str(self.root))

    def test_invalid_folder_pattern_keeps_existing_settings(self):
        self.bridge.addIgnoreFolderPattern(r"/safe/")
        self.bridge.addIgnoreFolderPattern("[")
        self.assertEqual(self.bridge.get_ignore_folder_patterns(), [r"/safe/"])
        self.assertIn("Invalid folder regex", self.bridge.get_status_text())

    def test_smart_cleanup_excludes_other_folders_and_dissimilar_names(self):
        names = ("copy.txt", "copy (1).txt", "unrelated.txt", "nested/copy (2).txt")
        for name in names:
            path = self.root / name
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(b"same")
        os.utime(self.root / "copy.txt", (100, 100))
        os.utime(self.root / "copy (1).txt", (200, 200))
        os.utime(self.root / "unrelated.txt", (300, 300))
        self.bridge._complete_scan(scan_for_duplicates(self.root))
        self.assertEqual(self.bridge._collect_magic_cleanup_candidates(), [str(self.root / "copy (1).txt")])

    def test_stop_scan_finishes_with_stopped_state(self):
        entered = Event()

        def wait_until_cancelled(folder, *, should_cancel, **_options):
            entered.set()
            deadline = time.monotonic() + 5
            while not should_cancel() and time.monotonic() < deadline:
                time.sleep(0.005)
            if not should_cancel():
                raise AssertionError("Scan worker did not receive cancellation")
            return scan_for_duplicates(folder, should_cancel=lambda: True)

        self.bridge.setSelectedFolder(str(self.root))
        with patch("duplicate_cleaner.bridge.scan_for_duplicates", side_effect=wait_until_cancelled):
            self.bridge.startScan()
            self.assertTrue(entered.wait(2))
            self.bridge.stopScan()
            self.assertTrue(self.bridge.get_is_cancelling())
            self.wait_scan()
        self.assertEqual(self.bridge.get_scan_summary()["phase"], "Stopped")
        self.assertEqual(self.bridge.get_duplicate_groups(), [])
        self.assertFalse(self.bridge.get_is_cancelling())

    def test_scan_failure_clears_worker_state(self):
        self.bridge.setSelectedFolder(str(self.root))
        with patch("duplicate_cleaner.bridge.scan_for_duplicates", side_effect=PermissionError("access denied")):
            self.bridge.startScan()
            self.wait_scan()
        self.assertEqual(self.bridge.get_scan_summary()["phase"], "Failed")
        self.assertIn("access denied", self.bridge.get_status_text())
        self.assertIsNone(self.bridge._scan_worker)

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
