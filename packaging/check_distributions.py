"""Check release contents against this checkout; this is not a license audit."""
from email.parser import BytesParser
from pathlib import Path
import sys
import tarfile
import tomllib
from zipfile import ZipFile

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def legal_files(root: Path) -> list[Path]:
    return [root / name for name in ("LICENSE", "THIRD_PARTY_NOTICES", "LICENSE_AUDIT.md")] + sorted(
        path for path in (root / "LICENSES").iterdir() if path.is_file()
    )


def check(directory: Path, root: Path = PROJECT_ROOT) -> None:
    version = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    wheels = sorted(directory.glob("duplicate_cleaner-*.whl"))
    sources = sorted(directory.glob("duplicate_cleaner-*.tar.gz"))
    if len(wheels) != 1 or len(sources) != 1:
        raise ValueError("Expected exactly one wheel and one source archive")
    legal = {path.relative_to(root).as_posix(): path.read_bytes() for path in legal_files(root)}
    assets = {
        "duplicate_cleaner/resources/" + path.relative_to(root).as_posix(): path.read_bytes()
        for path in (root / "qml").rglob("*.qml")
    }
    assets.update({
        "duplicate_cleaner/resources/assets/" + path.name: path.read_bytes()
        for path in (root / "packaging/assets").iterdir() if path.is_file()
    })
    info = f"duplicate_cleaner-{version}.dist-info"
    with ZipFile(wheels[0]) as archive:
        if len(set(archive.namelist())) != len(archive.namelist()):
            raise ValueError("Wheel contains duplicate entries")
        try:
            metadata = BytesParser().parsebytes(archive.read(f"{info}/METADATA"))
            if metadata.get_all("License-Expression") != ["MIT"]:
                raise ValueError("Wheel must declare exactly the MIT project license")
            if metadata.get("Version") != version:
                raise ValueError("Wheel version does not match the project")
            if set(metadata.get_all("License-File", [])) != set(legal):
                raise ValueError("Wheel license-file declarations do not match the project")
            for name, expected in {**assets, **{f"{info}/licenses/{n}": b for n, b in legal.items()}}.items():
                if archive.read(name) != expected:
                    raise ValueError(f"Wheel has stale or altered content: {name}")
        except KeyError as error:
            raise ValueError(f"Wheel is missing required content: {error}") from error
    with tarfile.open(sources[0], "r:gz") as archive:
        members = archive.getmembers()
        if len({item.name for item in members}) != len(members):
            raise ValueError("Source archive contains duplicate entries")
        required = dict(legal)
        required.update({name: (root / name).read_bytes() for name in ("SECURITY.md", "TEST_PLAN.md")})
        for name, expected in required.items():
            archive_name = f"duplicate_cleaner-{version}/{name}"
            try:
                member = archive.getmember(archive_name)
            except KeyError as error:
                raise ValueError(f"Source archive is missing {name}") from error
            if not member.isfile():
                raise ValueError(f"Source archive must contain a regular file: {name}")
            with archive.extractfile(member) as stream:
                if stream.read() != expected:
                    raise ValueError(f"Source archive has stale or altered content: {name}")
    print("Distribution contents match project assets and legal documents; binary license audit is separate.")


if __name__ == "__main__":
    try:
        check(Path(sys.argv[1] if len(sys.argv) > 1 else "dist"))
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error
