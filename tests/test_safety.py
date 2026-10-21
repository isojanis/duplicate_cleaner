"""Filesystem changes between discovery and reading must invalidate scan evidence."""
import unittest
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from duplicate_cleaner.safety import fingerprint, verified_copy
from duplicate_cleaner.scanner import _file_hash, scan_for_duplicates


class FileIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "candidate"
        self.path.write_bytes(b"same")
        self.other = self.root / "other-file"
        self.other.write_bytes(b"same")

    def test_verified_copy_accepts_unchanged_file(self):
        self.assertTrue(verified_copy(self.path, fingerprint(self.path), sha256(b"same").hexdigest()))

    def test_verified_copy_rejects_replacement_after_path_check(self):
        expected = fingerprint(self.path)
        original_open = Path.open

        def replace_before_open(path, *args, **kwargs):
            return original_open(self.other if path == self.path else path, *args, **kwargs)
        with patch.object(Path, "open", replace_before_open):
            self.assertFalse(verified_copy(self.path, expected, sha256(b"same").hexdigest()))

    def test_scan_rejects_replacement_after_path_check(self):
        original_open = Path.open

        def replace_before_open(path, *args, **kwargs):
            return original_open(self.other if path == self.path else path, *args, **kwargs)
        with patch.object(Path, "open", replace_before_open):
            result = scan_for_duplicates(self.root)
        self.assertEqual(result["groupCount"], 0)
        self.assertEqual(result["skippedFiles"], 1)

    def test_hash_rejects_replacement_of_same_bytes(self):
        expected = fingerprint(self.path)
        original_open = Path.open

        def wrong_handle(path, *args, **kwargs):
            return original_open(self.other if path == self.path else path, *args, **kwargs)
        with patch.object(Path, "open", wrong_handle), self.assertRaises(OSError):
            _file_hash(self.path, expected=expected)
