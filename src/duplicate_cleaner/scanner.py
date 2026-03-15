from __future__ import annotations

import os
import time
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from typing import Callable

ProgressCallback = Callable[[dict[str, object]], None]
CancelCallback = Callable[[], bool]

PROGRESS_INTERVAL_SECONDS = 0.1


def _file_hash(
    path: Path,
    chunk_size: int = 1024 * 1024,
    should_cancel: CancelCallback | None = None,
) -> str | None:
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            if should_cancel is not None and should_cancel():
                return None
            digest.update(chunk)
    return digest.hexdigest()


def _cancelled_result(
    folder: Path,
    *,
    total_files: int,
    total_folders: int,
    skipped_files: int,
    current_path: str,
    live_group_count: int,
    live_duplicate_files: int,
) -> dict[str, object]:
    return {
        "cancelled": True,
        "folder": str(folder),
        "currentPath": current_path,
        "totalFiles": total_files,
        "totalFolders": total_folders,
        "skippedFiles": skipped_files,
        "groupCount": live_group_count,
        "duplicateFiles": live_duplicate_files,
        "wastedBytes": 0,
        "groups": [],
    }


def scan_for_duplicates(
    folder: Path,
    *,
    progress_callback: ProgressCallback | None = None,
    should_cancel: CancelCallback | None = None,
    ignore_empty_files: bool = True,
    ignore_large_files: bool = False,
    max_file_size_bytes: int = 1024 * 1024 * 1024,
    duplicate_search_limit: int = 10_000,
) -> dict[str, object]:
    files_by_size: dict[int, list[Path]] = defaultdict(list)
    total_files = 0
    total_folders = 0
    skipped_files = 0
    current_path = str(folder)
    live_group_count = 0
    live_duplicate_files = 0
    hash_candidates = 0
    hashed_files = 0
    last_progress_at = 0.0
    search_limit_reached = False

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
                "hashedFiles": hashed_files,
            }
        )

    def handle_walk_error(_error: OSError) -> None:
        nonlocal skipped_files
        skipped_files += 1
        emit_progress("Skipping unreadable entry...", force=True)

    for root_path, _dirnames, filenames in os.walk(folder, onerror=handle_walk_error):
        if should_cancel is not None and should_cancel():
            return _cancelled_result(
                folder,
                total_files=total_files,
                total_folders=total_folders,
                skipped_files=skipped_files,
                current_path=current_path,
                live_group_count=live_group_count,
                live_duplicate_files=live_duplicate_files,
            )

        total_folders += 1
        current_path = root_path
        emit_progress("Scanning folder...")

        current_root = Path(root_path)
        for filename in filenames:
            if should_cancel is not None and should_cancel():
                return _cancelled_result(
                    folder,
                    total_files=total_files,
                    total_folders=total_folders,
                    skipped_files=skipped_files,
                    current_path=current_path,
                    live_group_count=live_group_count,
                    live_duplicate_files=live_duplicate_files,
                )

            path = current_root / filename
            current_path = str(path)

            try:
                size = path.stat().st_size
            except OSError:
                skipped_files += 1
                emit_progress("Skipping unreadable file...", force=True)
                continue

            if not path.is_file():
                continue

            if ignore_empty_files and size == 0:
                emit_progress("Ignoring empty file...")
                continue

            if ignore_large_files and size > max_file_size_bytes:
                emit_progress("Ignoring file larger than configured limit...")
                continue

            total_files += 1
            files_by_size[size].append(path)
            emit_progress("Scanning file...")

    hash_candidates = sum(len(paths) for paths in files_by_size.values() if len(paths) > 1)
    duplicate_groups: list[dict[str, object]] = []
    emit_progress("Preparing duplicate check...", force=True)

    for size, paths in files_by_size.items():
        if len(paths) < 2:
            continue

        files_by_hash: dict[str, list[Path]] = defaultdict(list)
        for path in paths:
            if hashed_files >= duplicate_search_limit:
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
                    live_group_count=live_group_count,
                    live_duplicate_files=live_duplicate_files,
                )

            current_path = str(path)
            try:
                file_hash = _file_hash(path, should_cancel=should_cancel)
            except OSError:
                skipped_files += 1
                emit_progress("Skipping unreadable file during hashing...", force=True)
                continue

            if file_hash is None:
                return _cancelled_result(
                    folder,
                    total_files=total_files,
                    total_folders=total_folders,
                    skipped_files=skipped_files,
                    current_path=current_path,
                    live_group_count=live_group_count,
                    live_duplicate_files=live_duplicate_files,
                )

            files_by_hash[file_hash].append(path)
            group_size = len(files_by_hash[file_hash])
            if group_size == 2:
                live_group_count += 1
                live_duplicate_files += 2
            elif group_size > 2:
                live_duplicate_files += 1

            hashed_files += 1
            emit_progress("Hashing duplicate candidates...")

        for matching_paths in files_by_hash.values():
            if len(matching_paths) < 2:
                continue

            sorted_paths = sorted(matching_paths)
            duplicate_groups.append(
                {
                    "count": len(sorted_paths),
                    "sizeBytes": size,
                    "wastedBytes": size * (len(sorted_paths) - 1),
                    "files": [str(path) for path in sorted_paths],
                }
            )

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
