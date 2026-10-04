"""Exercise portable ZIP rejection paths without executing fixture binaries."""
import hashlib
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest
import zipfile


POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")
VALIDATOR = Path(__file__).resolve().parents[1] / "packaging/windows/validate-portable.ps1"


@unittest.skipUnless(POWERSHELL, "PowerShell required for Windows archive validation")
class WindowsArchiveTests(unittest.TestCase):
    def validate_fixture(self, *, missing=None, corrupt_checksum=False):
        with TemporaryDirectory() as tmp:
            archive = Path(tmp) / "DuplicateCleaner-test.zip"
            files = (
                "DuplicateCleaner.exe", "_internal/LICENSE", "_internal/README.md",
                "_internal/duplicate_cleaner/resources/qml/Main.qml",
                "_internal/duplicate_cleaner/resources/qml/components/ResultsPane.qml",
                "_internal/duplicate_cleaner/resources/assets/duplicate-cleaner.svg",
            )
            with zipfile.ZipFile(archive, "w") as bundle:
                for name in files:
                    if name != missing:
                        bundle.writestr(f"DuplicateCleaner/{name}", b"fixture only")
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            if corrupt_checksum:
                digest = "0" * 64
            Path(f"{archive}.sha256").write_text(f"{digest}  {archive.name}\n", encoding="ascii")
            result = subprocess.run(
                [POWERSHELL, "-NoProfile", "-File", str(VALIDATOR), "-Archive", str(archive)],
                capture_output=True, text=True, timeout=30,
            )
            self.assertNotEqual(result.returncode, 0)
            return result.stdout + result.stderr

    def test_corrupt_checksum_is_rejected_before_launch(self):
        self.assertIn("checksum does not match", self.validate_fixture(corrupt_checksum=True))

    def test_missing_license_is_rejected_before_launch(self):
        self.assertIn("missing _internal/LICENSE", self.validate_fixture(missing="_internal/LICENSE"))

    def test_missing_qml_is_rejected_before_launch(self):
        path = "_internal/duplicate_cleaner/resources/qml/Main.qml"
        output = self.validate_fixture(missing=path)
        self.assertIn("missing", output)
        self.assertIn(path, output)
