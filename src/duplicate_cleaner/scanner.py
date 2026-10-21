from __future__ import annotations

import os
import re
import stat
import time
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from typing import Callable

from .safety import _stat_fingerprint, fingerprint

ProgressCallback = Callable[[dict[str, object]], None]
CancelCallback = Callable[[], bool]
HashProgressCallback = Callable[[int], None]

PROGRESS_INTERVAL_SECONDS = 0.1


def _is_link_directory(path: Path) -> bool:
    """Exclude symlinks and Windows junctions, including on Python 3.11."""
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or (
        getattr(info, "st_reparse_tag", 0)
        == getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003)
    )


def _file_hash(
    path: Path,
    chunk_size: int = 1024 * 1024,
    should_cancel: CancelCallback | None = None,
    progress_callback: HashProgressCallback | None = None,
    expected: tuple[int, int, int, int, int] | None = None,
) -> str | None:
    digest = sha256()
    bytes_read = 0
    with path.open("rb") as handle:
        if expected is not None and _stat_fingerprint(os.fstat(handle.fileno())) != expected:
            raise OSError("File changed before hashing")
        while chunk := handle.read(chunk_size):
            if should_cancel is not None and should_cancel():
                return None
            digest.update(chunk)
            bytes_read += len(chunk)
            if progress_callback is not None:
                progress_callback(bytes_read)
        if expected is not None and _stat_fingerprint(os.fstat(handle.fileno())) != expected:
            raise OSError("File changed while hashing")
    return digest.hexdigest()


def _cancelled_result(
    folder: Path,
    *,
    total_files: int,
    total_folders: int,
    skipped_files: int,
    current_path: str,
    groups: list[dict[str, object]],
) -> dict[str, object]:
    sorted_groups = sorted(
        groups,
        key=lambda group: (group["wastedBytes"], group["count"]),
        reverse=True,
    )
    return {
        "cancelled": True,
        "folder": str(folder),
        "currentPath": current_path,
        "totalFiles": total_files,
        "totalFolders": total_folders,
        "skippedFiles": skipped_files,
        "groupCount": len(sorted_groups),
        "duplicateFiles": sum(group["count"] for group in sorted_groups),
        "wastedBytes": sum(group["wastedBytes"] for group in sorted_groups),
        "groups": sorted_groups,
    }


def _matching_groups_for_size(size: int, files_by_hash: dict[str, list[Path]]) -> list[dict[str, object]]:
    duplicate_groups: list[dict[str, object]] = []
    for digest, matching_paths in files_by_hash.items():
        if len(matching_paths) < 2:
            continue

        sorted_paths = sorted(matching_paths)
        duplicate_groups.append(
            {
                "count": len(sorted_paths),
                "sizeBytes": size,
                "wastedBytes": size * (len(sorted_paths) - 1),
                "files": [str(path) for path in sorted_paths],
                "hash": digest,
            }
        )

    return duplicate_groups


def scan_for_duplicates(
    folder: Path,
    *,
    progress_callback: ProgressCallback | None = None,
    should_cancel: CancelCallback | None = None,
    ignore_empty_files: bool = True,
    include_subfolders: bool = True,
    limit_file_size_range: bool = False,
    min_file_size_bytes: int = 1,
    max_file_size_bytes: int = 1024 * 1024 * 1024,
    use_duplicate_search_limit: bool = True,
    duplicate_search_limit: int = 10_000,
    use_ignore_folder_patterns: bool = False,
    ignore_folder_patterns: list[str] | None = None,
    use_ignore_file_extensions: bool = False,
    ignore_file_extensions: list[str] | None = None,
    use_only_search_file_extension: bool = False,
    only_search_file_extension: str = "",
) -> dict[str, object]:
    folder = folder.expanduser().absolute()
    if not folder.is_dir():
        raise ValueError(f"Not a directory: {folder}")
    files_by_size: dict[int, list[Path]] = defaultdict(list)
    snapshots: dict[str, tuple] = {}
    seen_inodes: set[tuple[int, int]] = set()
    total_files = 0
    total_folders = 0
    skipped_files = 0
    current_path = str(folder)
    live_group_count = 0
    live_duplicate_files = 0
    hash_candidates = 0
    hash_work_candidates = 0
    hashed_files = 0
    hash_candidates_processed = 0
    hash_bytes_processed = 0
    hash_total_bytes = 0
    current_file_bytes = 0
    current_file_size = 0
    last_progress_at = 0.0
    search_limit_reached = False
    compiled_ignore_folder_patterns = [
        re.compile(pattern) for pattern in (ignore_folder_patterns or []) if pattern
    ] if use_ignore_folder_patterns else []
    ignored_extensions = {extension.lower() for extension in (ignore_file_extensions or []) if extension} if use_ignore_file_extensions else set()
    required_extension = only_search_file_extension.lower() if use_only_search_file_extension and only_search_file_extension else ""

    def emit_progress(phase: str, *, force: bool = False) -> None:
        nonlocal last_progress_at
        if progress_callback is None:
            return

        now = time.monotonic()
        if not force and now - last_progress_at < PROGRESS_INTERVAL_SECONDS:
            return

        last_progress_at = now
        progress_callback(
            {
                "phase": phase,
                "currentPath": current_path,
                "totalFiles": total_files,
                "totalFolders": total_folders,
                "skippedFiles": skipped_files,
                "liveGroupCount": live_group_count,
                "liveDuplicateFiles": live_duplicate_files,
                "hashCandidates": hash_candidates,
                "hashWorkCandidates": hash_work_candidates,
                "hashedFiles": hashed_files,
                "hashCandidatesProcessed": hash_candidates_processed,
                "hashBytesProcessed": hash_bytes_processed,
                "hashTotalBytes": hash_total_bytes,
                "currentFileBytes": current_file_bytes,
                "currentFileSize": current_file_size,
            }
        )

    def handle_walk_error(_error: OSError) -> None:
        nonlocal skipped_files
        skipped_files += 1
        emit_progress("Skipping unreadable entry...")

    for root_path, dirnames, filenames in os.walk(folder, onerror=handle_walk_error):
        current_root = Path(root_path)
        if include_subfolders:
            filtered_dirnames: list[str] = []
            for dirname in dirnames:
                directory_path = current_root / dirname
                try:
                    is_link = _is_link_directory(directory_path)
                except OSError as exc:
                    handle_walk_error(exc)
                    continue
                if is_link:
                    continue
                directory_text = directory_path.as_posix() + "/"
                if any(pattern.search(directory_text) for pattern in compiled_ignore_folder_patterns):
                    continue
                filtered_dirnames.append(dirname)
            dirnames[:] = filtered_dirnames
        else:
            dirnames[:] = []
        if should_cancel is not None and should_cancel():
            return _cancelled_result(
                folder,
                total_files=total_files,
                total_folders=total_folders,
                skipped_files=skipped_files,
                current_path=current_path,
                groups=[],
            )

        total_folders += 1
        current_path = root_path
        emit_progress("Scanning folder...")

        for filename in filenames:
            if should_cancel is not None and should_cancel():
                return _cancelled_result(
                    folder,
                    total_files=total_files,
                    total_folders=total_folders,
                    skipped_files=skipped_files,
                    current_path=current_path,
                    groups=[],
                )

            path = current_root / filename
            current_path = str(path)

            try:
                identity = fingerprint(path)
                size = identity[2]
            except OSError:
                skipped_files += 1
                emit_progress("Skipping unreadable file...")
                continue

            if not path.is_file():
                continue

            inode = identity[:2]
            if inode[1] and inode in seen_inodes:
                continue
            seen_inodes.add(inode)
            snapshots[str(path)] = identity

            if ignore_empty_files and size == 0:
                emit_progress("Ignoring empty file...")
                continue

            if required_extension and path.suffix.lower() != required_extension:
                emit_progress("Ignoring file outside required extension filter...")
                continue

            if path.suffix.lower() in ignored_extensions:
                emit_progress("Ignoring file with excluded extension...")
                continue

            if limit_file_size_range and (size < min_file_size_bytes or size > max_file_size_bytes):
                emit_progress("Ignoring file outside configured size range...")
                continue

            total_files += 1
            files_by_size[size].append(path)
            emit_progress("Scanning file...")

    hash_candidates = sum(len(paths) for paths in files_by_size.values() if len(paths) > 1)
    hash_work_candidates = (
        min(hash_candidates, max(0, duplicate_search_limit))
        if use_duplicate_search_limit
        else hash_candidates
    )
    remaining_hash_candidates = (
        max(0, duplicate_search_limit)
        if use_duplicate_search_limit
        else hash_candidates
    )
    for size, paths in files_by_size.items():
        if len(paths) < 2 or remaining_hash_candidates <= 0:
            continue
        candidates_in_group = min(len(paths), remaining_hash_candidates)
        hash_total_bytes += size * candidates_in_group
        remaining_hash_candidates -= candidates_in_group

    duplicate_groups: list[dict[str, object]] = []
    def matching_groups(size: int, hashes: dict[str, list[Path]]) -> list[dict[str, object]]:
        groups = _matching_groups_for_size(size, hashes)
        for group in groups:
            group["snapshots"] = {path: snapshots[path] for path in group["files"]}
        return groups
    emit_progress("Preparing duplicate check...", force=True)

    for size, paths in files_by_size.items():
        if len(paths) < 2:
            continue

        files_by_hash: dict[str, list[Path]] = defaultdict(list)
        for path in paths:
            if use_duplicate_search_limit and hash_candidates_processed >= duplicate_search_limit:
                search_limit_reached = True
                emit_progress("Reached duplicate search limit.", force=True)
                break
            if should_cancel is not None and should_cancel():
                return _cancelled_result(
                    folder,
                    total_files=total_files,
                    total_folders=total_folders,
                    skipped_files=skipped_files,
                    current_path=current_path,
                    groups=duplicate_groups + matching_groups(size, files_by_hash),
                )

            current_path = str(path)
            current_file_bytes = 0
            current_file_size = size

            def report_hash_progress(bytes_read: int) -> None:
                nonlocal current_file_bytes
                current_file_bytes = bytes_read
                emit_progress("Hashing duplicate candidates...")

            try:
                if fingerprint(path) != snapshots[str(path)]:
                    raise OSError("File changed since discovery")
                file_hash = _file_hash(
                    path,
                    should_cancel=should_cancel,
                    progress_callback=report_hash_progress,
                    expected=snapshots[str(path)],
                )
                if fingerprint(path) != snapshots[str(path)]:
                    raise OSError("File changed while hashing")
            except OSError:
                skipped_files += 1
                hash_candidates_processed += 1
                hash_bytes_processed += current_file_bytes
                current_file_bytes = 0
                current_file_size = 0
                emit_progress("Skipping unreadable file during hashing...")
                continue

            if file_hash is None:
                emit_progress("Stopping scan...", force=True)
                return _cancelled_result(
                    folder,
                    total_files=total_files,
                    total_folders=total_folders,
                    skipped_files=skipped_files,
                    current_path=current_path,
                    groups=duplicate_groups + matching_groups(size, files_by_hash),
                )

            files_by_hash[file_hash].append(path)
            group_size = len(files_by_hash[file_hash])
            if group_size == 2:
                live_group_count += 1
                live_duplicate_files += 2
            elif group_size > 2:
                live_duplicate_files += 1

            hashed_files += 1
            hash_candidates_processed += 1
            hash_bytes_processed += size
            current_file_bytes = 0
            current_file_size = 0
            emit_progress("Hashing duplicate candidates...")

        duplicate_groups.extend(matching_groups(size, files_by_hash))

        if search_limit_reached:
            duplicate_groups.sort(
                key=lambda group: (group["wastedBytes"], group["count"]),
                reverse=True,
            )
            emit_progress("Duplicate search limit reached.", force=True)
            return {
                "cancelled": False,
                "folder": str(folder),
                "currentPath": current_path,
                "totalFiles": total_files,
                "totalFolders": total_folders,
                "skippedFiles": skipped_files,
                "groupCount": len(duplicate_groups),
                "duplicateFiles": sum(group["count"] for group in duplicate_groups),
                "wastedBytes": sum(group["wastedBytes"] for group in duplicate_groups),
                "groups": duplicate_groups,
                "searchLimitReached": True,
            }

    duplicate_groups.sort(
        key=lambda group: (group["wastedBytes"], group["count"]),
        reverse=True,
    )

    if search_limit_reached:
        emit_progress("Duplicate search limit reached.", force=True)
    else:
        emit_progress("Scan complete.", force=True)

    return {
        "cancelled": False,
        "folder": str(folder),
        "currentPath": current_path,
        "totalFiles": total_files,
        "totalFolders": total_folders,
        "skippedFiles": skipped_files,
        "groupCount": len(duplicate_groups),
        "duplicateFiles": sum(group["count"] for group in duplicate_groups),
        "wastedBytes": sum(group["wastedBytes"] for group in duplicate_groups),
        "groups": duplicate_groups,
        "searchLimitReached": search_limit_reached,
    }
