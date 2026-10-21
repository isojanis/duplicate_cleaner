"""Fail release builds that omit the UI or required legal documents."""
import sys
import tarfile
from pathlib import Path
from zipfile import ZipFile


def check(directory: Path) -> None:
    wheels = sorted(directory.glob("duplicate_cleaner-*.whl"))
    sources = sorted(directory.glob("duplicate_cleaner-*.tar.gz"))
    if len(wheels) != 1 or len(sources) != 1:
        raise ValueError("Expected exactly one wheel and one source archive")

    with ZipFile(wheels[0]) as archive:
        names = set(archive.namelist())
        licenses = {name for name in names if ".dist-info/licenses/" in name}
        for suffix in ("LICENSE", "THIRD_PARTY_NOTICES"):
            if not any(name.endswith("/" + suffix) for name in licenses):
                raise ValueError(f"Wheel is missing {suffix}")
        for suffix in ("resources/qml/Main.qml", "resources/assets/duplicate-cleaner.svg"):
            if not any(name.endswith(suffix) for name in names):
                raise ValueError(f"Wheel is missing {suffix}")
        metadata_name = next((name for name in names if name.endswith(".dist-info/METADATA")), None)
        if metadata_name is None or "License-Expression: MIT" not in archive.read(metadata_name).decode():
            raise ValueError("Wheel is missing MIT license metadata")

    with tarfile.open(sources[0], "r:gz") as archive:
        names = {Path(name).name for name in archive.getnames()}
        for name in ("LICENSE", "THIRD_PARTY_NOTICES", "SECURITY.md", "TEST_PLAN.md"):
            if name not in names:
                raise ValueError(f"Source archive is missing {name}")
    print("Distribution UI, legal files, and license metadata verified.")


if __name__ == "__main__":
    try:
        check(Path(sys.argv[1] if len(sys.argv) > 1 else "dist"))
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error
