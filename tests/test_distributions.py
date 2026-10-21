"""Release-content checks must reject misleading or incomplete legal payloads."""
import importlib.util
import io
from pathlib import Path
import tarfile
from tempfile import TemporaryDirectory
import tomllib
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_distributions", ROOT / "packaging/check_distributions.py")
CHECKS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKS)


class DistributionTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name)
        self.version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
        self.info = f"duplicate_cleaner-{self.version}.dist-info"

    def build_fixture(self, *, omit=None, altered=None, expression="MIT", misplaced_source=False):
        legal = {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in CHECKS.legal_files(ROOT)}
        metadata = f"Metadata-Version: 2.4\nVersion: {self.version}\nLicense-Expression: {expression}\n"
        metadata += "".join(f"License-File: {name}\n" for name in legal)
        files = {f"{self.info}/METADATA": metadata.encode()}
        files.update({f"{self.info}/licenses/{name}": data for name, data in legal.items()})
        files.update({"duplicate_cleaner/resources/" + p.relative_to(ROOT).as_posix(): p.read_bytes()
                      for p in (ROOT / "qml").rglob("*.qml")})
        files.update({"duplicate_cleaner/resources/assets/" + p.name: p.read_bytes()
                      for p in (ROOT / "packaging/assets").iterdir() if p.is_file()})
        if altered:
            files[altered] = b"Old notice text from another release\n"
        with ZipFile(self.output / f"duplicate_cleaner-{self.version}-py3-none-any.whl", "w") as archive:
            for name, data in files.items():
                if name != omit:
                    archive.writestr(name, data)
        legal.update({name: (ROOT / name).read_bytes() for name in ("SECURITY.md", "TEST_PLAN.md")})
        with tarfile.open(self.output / f"duplicate_cleaner-{self.version}.tar.gz", "w:gz") as archive:
            for name, data in legal.items():
                if misplaced_source and name == "LICENSE":
                    name = "unrelated/LICENSE"
                entry = tarfile.TarInfo(f"duplicate_cleaner-{self.version}/{name}")
                entry.size = len(data)
                archive.addfile(entry, io.BytesIO(data))

    def test_matching_documents_and_assets_pass(self):
        self.build_fixture()
        CHECKS.check(self.output)

    def test_missing_lgpl_text_is_rejected(self):
        self.build_fixture(omit=f"{self.info}/licenses/LICENSES/LGPL-3.0-only.txt")
        with self.assertRaisesRegex(ValueError, "missing required content"):
            CHECKS.check(self.output)

    def test_stale_notice_is_rejected(self):
        self.build_fixture(altered=f"{self.info}/licenses/THIRD_PARTY_NOTICES")
        with self.assertRaisesRegex(ValueError, "stale or altered"):
            CHECKS.check(self.output)

    def test_license_expression_prefix_does_not_pass(self):
        self.build_fixture(expression="MIT OR GPL-3.0-only")
        with self.assertRaisesRegex(ValueError, "exactly the MIT"):
            CHECKS.check(self.output)

    def test_unrelated_nested_license_does_not_replace_project_license(self):
        self.build_fixture(misplaced_source=True)
        with self.assertRaisesRegex(ValueError, "Source archive is missing LICENSE"):
            CHECKS.check(self.output)

    def test_missing_qml_component_is_rejected(self):
        self.build_fixture(omit="duplicate_cleaner/resources/qml/components/PreviewPane.qml")
        with self.assertRaisesRegex(ValueError, "missing required content"):
            CHECKS.check(self.output)
