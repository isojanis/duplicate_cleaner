from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from duplicate_cleaner.scanner import scan_for_duplicates
from duplicate_cleaner.safety import validate_removal


class ScannerTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, content=b"same"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def scan(self, **kwargs):
        return scan_for_duplicates(self.root, **kwargs)

    def test_content_groups_and_accounting(self):
        for name in ("a.txt", "b.txt", "nested/c.txt"):
            self.write(name)
        self.write("different.txt", b"diff")
        result = self.scan()
        self.assertEqual((result["groupCount"], result["duplicateFiles"], result["wastedBytes"]), (1, 3, 8))
        group = result["groups"][0]
        self.assertEqual(len(group["snapshots"]), 3)
        self.assertEqual(len(group["hash"]), 64)

    def test_filters(self):
        self.write("a.txt")
        self.write("nested/b.TXT")
        self.write("c.bin")
        self.write("empty1", b"")
        self.write("empty2", b"")
        cases = [
            ({"include_subfolders": False}, 2),
            ({"use_only_search_file_extension": True, "only_search_file_extension": ".txt"}, 2),
            ({"use_ignore_file_extensions": True, "ignore_file_extensions": [".txt"]}, 0),
            ({"use_ignore_folder_patterns": True, "ignore_folder_patterns": ["/nested/"]}, 2),
            ({"limit_file_size_range": True, "min_file_size_bytes": 5}, 0),
        ]
        for options, expected in cases:
            with self.subTest(options=options):
                self.assertEqual(self.scan(**options)["duplicateFiles"], expected)
        self.assertEqual(self.scan(ignore_empty_files=False)["groupCount"], 2)

    def test_limit_and_cancel(self):
        for name in ("a", "b", "c"):
            self.write(name)
        result = self.scan(duplicate_search_limit=1)
        self.assertTrue(result["searchLimitReached"])
        self.assertEqual(result["groupCount"], 0)
        self.assertTrue(self.scan(should_cancel=lambda: True)["cancelled"])

    def test_cancel_during_hashing_retains_verified_groups(self):
        for name in ("a", "b", "c"):
            self.write(name)
        progress = {}
        def update(value):
            progress.update(value)
        with patch("duplicate_cleaner.scanner.PROGRESS_INTERVAL_SECONDS", 0):
            result = self.scan(progress_callback=update, should_cancel=lambda: progress.get("hashedFiles", 0) >= 2)
        self.assertTrue(result["cancelled"])
        self.assertEqual(result["duplicateFiles"], 2)
        self.assertEqual(len(result["groups"][0]["snapshots"]), 2)

    def test_invalid_root(self):
        with self.assertRaises(ValueError):
            scan_for_duplicates(self.root / "missing")

    def test_links_do_not_inflate_reclaimable_space(self):
        original = self.write("original")
        try:
            (self.root / "hardlink").hardlink_to(original)
            (self.root / "symlink").symlink_to(original)
        except OSError:
            self.skipTest("Link creation unavailable")
        self.assertEqual(self.scan()["groupCount"], 0)

    def test_changed_during_hash_is_skipped(self):
        first = self.write("a")
        self.write("b")
        from duplicate_cleaner.scanner import _file_hash
        def mutate(path, **kwargs):
            digest = _file_hash(path, **kwargs)
            if path == first:
                path.write_bytes(b"changed")
            return digest
        with patch("duplicate_cleaner.scanner._file_hash", side_effect=mutate):
            result = self.scan()
        self.assertEqual(result["groupCount"], 0)
        self.assertEqual(result["skippedFiles"], 1)

    def test_removal_requires_unchanged_survivor(self):
        a, b = self.write("a"), self.write("b")
        group = self.scan()["groups"][0]
        validate_removal(a, group, [])
        with self.assertRaises(ValueError):
            validate_removal(a, group, [str(b)])
        b.write_bytes(b"diff")
        with self.assertRaises(ValueError):
            validate_removal(a, group, [])

    def test_changed_target_is_not_removed(self):
        a = self.write("a")
        self.write("b")
        group = self.scan()["groups"][0]
        a.write_bytes(b"diff")
        with self.assertRaises(ValueError):
            validate_removal(a, group, [])
