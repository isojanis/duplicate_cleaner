"""Validate scan evidence again before removing a duplicate."""
from hashlib import sha256
from pathlib import Path
import stat


def fingerprint(path: Path) -> tuple[int, int, int, int, int]:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise OSError("Not a regular file (links are excluded).")
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def verified_copy(path: Path, expected: tuple, digest: str, should_cancel=None) -> bool:
    try:
        if fingerprint(path) != tuple(expected):
            return False
        value = sha256()
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                if should_cancel and should_cancel():
                    raise InterruptedError("Cleanup cancelled")
                value.update(chunk)
        return value.hexdigest() == digest and fingerprint(path) == tuple(expected)
    except InterruptedError:
        raise
    except OSError:
        return False


def validate_removal(path: Path, group: dict, deleted: list[str], should_cancel=None) -> None:
    """Refuse stale evidence, unknown paths, links, and the final surviving copy."""
    snapshots = group.get("snapshots", {})
    digest = group.get("hash", "")
    expected = snapshots.get(str(path))
    if not expected or not digest or not verified_copy(path, expected, digest, should_cancel):
        raise ValueError("File changed or is unavailable. Scan again before cleanup.")
    for other in group["files"]:
        if other == str(path) or other in deleted or other not in snapshots:
            continue
        if verified_copy(Path(other), snapshots[other], digest, should_cancel):
            # Detect changes during verification of the retained copy too.
            if fingerprint(path) != tuple(expected):
                break
            return
    raise ValueError("No unchanged duplicate remains. The last copy will not be removed.")
