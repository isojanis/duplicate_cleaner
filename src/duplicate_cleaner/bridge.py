from __future__ import annotations

from pathlib import Path
import re
import math
from threading import Event

from PySide6.QtCore import QObject, Property, QSettings, QThread, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

DEFAULT_MIN_FILE_SIZE_BYTES = 1
DEFAULT_MAX_FILE_SIZE_BYTES = 1024 * 1024 * 1024
DEFAULT_DUPLICATE_SEARCH_LIMIT = 1_000

from .scanner import scan_for_duplicates
from .safety import fingerprint
from .cleanup import CleanupWorker

RECENT_FOLDERS_KEY = "recentFolders"
IGNORE_EMPTY_FILES_KEY = "ignoreEmptyFiles"
INCLUDE_SUBFOLDERS_KEY = "includeSubfolders"
LIMIT_FILE_SIZE_RANGE_KEY = "limitFileSizeRange"
MIN_FILE_SIZE_BYTES_KEY = "minFileSizeBytes"
MAX_FILE_SIZE_BYTES_KEY = "maxFileSizeBytes"
USE_DUPLICATE_SEARCH_LIMIT_KEY = "useDuplicateSearchLimit"
DUPLICATE_SEARCH_LIMIT_KEY = "duplicateSearchLimit"
USE_IGNORE_FOLDER_PATTERNS_KEY = "useIgnoreFolderPatterns"
IGNORE_FOLDER_PATTERNS_KEY = "ignoreFolderPatterns"
USE_IGNORE_FILE_EXTENSIONS_KEY = "useIgnoreFileExtensions"
IGNORE_FILE_EXTENSIONS_KEY = "ignoreFileExtensions"
USE_ONLY_SEARCH_FILE_EXTENSION_KEY = "useOnlySearchFileExtension"
ONLY_SEARCH_FILE_EXTENSION_KEY = "onlySearchFileExtension"
MAX_RECENT_FOLDERS = 10
MAX_TEXT_PREVIEW_BYTES = 100_000
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"}
PDF_SUFFIXES = {".pdf"}
TEXT_SUFFIXES = {
    ".txt", ".md", ".py", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".log", ".csv", ".qml", ".js", ".ts", ".html", ".htm", ".css", ".xml",
    ".sh", ".bash", ".zsh", ".c", ".cc", ".cpp", ".h", ".hpp", ".rs", ".java",
}


def _format_byte_count(value: int) -> str:
    amount = float(max(0, value))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if amount < 1024 or unit == "TB":
            return f"{int(amount)} {unit}" if unit == "B" else f"{amount:.1f} {unit}"
        amount /= 1024
    return f"{amount:.1f} TB"


class ScanWorker(QObject):
    progress = Signal(dict)
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, folder: str, *, ignore_empty_files: bool, include_subfolders: bool, limit_file_size_range: bool, min_file_size_bytes: int, max_file_size_bytes: int, use_duplicate_search_limit: bool, duplicate_search_limit: int, use_ignore_folder_patterns: bool, ignore_folder_patterns: list[str], use_ignore_file_extensions: bool, ignore_file_extensions: list[str], use_only_search_file_extension: bool, only_search_file_extension: str) -> None:
        super().__init__()
        self._folder = Path(folder).expanduser()
        self._ignore_empty_files = ignore_empty_files
        self._include_subfolders = include_subfolders
        self._limit_file_size_range = limit_file_size_range
        self._min_file_size_bytes = min_file_size_bytes
        self._max_file_size_bytes = max_file_size_bytes
        self._use_duplicate_search_limit = use_duplicate_search_limit
        self._duplicate_search_limit = duplicate_search_limit
        self._use_ignore_folder_patterns = use_ignore_folder_patterns
        self._ignore_folder_patterns = ignore_folder_patterns
        self._use_ignore_file_extensions = use_ignore_file_extensions
        self._ignore_file_extensions = ignore_file_extensions
        self._use_only_search_file_extension = use_only_search_file_extension
        self._only_search_file_extension = only_search_file_extension
        self._cancel_requested = Event()

    @Slot()
    def run(self) -> None:
        try:
            results = scan_for_duplicates(
                self._folder,
                progress_callback=self.progress.emit,
                should_cancel=self._cancel_requested.is_set,
                ignore_empty_files=self._ignore_empty_files,
                include_subfolders=self._include_subfolders,
                limit_file_size_range=self._limit_file_size_range,
                min_file_size_bytes=self._min_file_size_bytes,
                max_file_size_bytes=self._max_file_size_bytes,
                use_duplicate_search_limit=self._use_duplicate_search_limit,
                duplicate_search_limit=self._duplicate_search_limit,
                use_ignore_folder_patterns=self._use_ignore_folder_patterns,
                ignore_folder_patterns=self._ignore_folder_patterns,
                use_ignore_file_extensions=self._use_ignore_file_extensions,
                ignore_file_extensions=self._ignore_file_extensions,
                use_only_search_file_extension=self._use_only_search_file_extension,
                only_search_file_extension=self._only_search_file_extension,
            )
        except Exception as exc:  # pragma: no cover - defensive bridge layer
            self.failed.emit(str(exc))
            return

        self.finished.emit(results)

    @Slot()
    def cancel(self) -> None:
        self._cancel_requested.set()


class AppBridge(QObject):
    selectedFolderChanged = Signal()
    recentFoldersChanged = Signal()
    deletedPathsChanged = Signal()
    previewDataChanged = Signal()
    ignoreEmptyFilesChanged = Signal()
    includeSubfoldersChanged = Signal()
    limitFileSizeRangeChanged = Signal()
    minFileSizeBytesChanged = Signal()
    maxFileSizeBytesChanged = Signal()
    useDuplicateSearchLimitChanged = Signal()
    duplicateSearchLimitChanged = Signal()
    useIgnoreFolderPatternsChanged = Signal()
    ignoreFolderPatternsChanged = Signal()
    useIgnoreFileExtensionsChanged = Signal()
    ignoreFileExtensionsChanged = Signal()
    useOnlySearchFileExtensionChanged = Signal()
    onlySearchFileExtensionChanged = Signal()
    statusTextChanged = Signal()
    duplicateGroupsChanged = Signal()
    magicCleanupChanged = Signal()
    sortFieldChanged = Signal()
    sortDirectionChanged = Signal()
    scanSummaryChanged = Signal()
    isScanningChanged = Signal()
    isCancellingChanged = Signal()
    isCleaningChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._settings = QSettings()
        self._recent_folders = self._load_recent_folders()
        self._deleted_paths: list[str] = []
        self._selected_folder = self._recent_folders[0] if self._recent_folders else str(Path.home())
        self._status_text = "Choose a folder to begin."
        self._duplicate_groups: list[dict[str, object]] = []
        self._preview_data = self._build_empty_preview()
        self._ignore_empty_files = self._load_bool_setting(IGNORE_EMPTY_FILES_KEY, True)
        self._include_subfolders = self._load_bool_setting(INCLUDE_SUBFOLDERS_KEY, True)
        self._limit_file_size_range = self._load_bool_setting(LIMIT_FILE_SIZE_RANGE_KEY, True)
        self._min_file_size_bytes = self._load_int_setting(MIN_FILE_SIZE_BYTES_KEY, DEFAULT_MIN_FILE_SIZE_BYTES)
        self._max_file_size_bytes = self._load_int_setting(MAX_FILE_SIZE_BYTES_KEY, DEFAULT_MAX_FILE_SIZE_BYTES)
        self._use_duplicate_search_limit = self._load_bool_setting(USE_DUPLICATE_SEARCH_LIMIT_KEY, True)
        self._duplicate_search_limit = self._load_int_setting(DUPLICATE_SEARCH_LIMIT_KEY, DEFAULT_DUPLICATE_SEARCH_LIMIT)
        self._use_ignore_folder_patterns = self._load_bool_setting(USE_IGNORE_FOLDER_PATTERNS_KEY, False)
        self._ignore_folder_patterns = self._load_list_setting(IGNORE_FOLDER_PATTERNS_KEY)
        self._use_ignore_file_extensions = self._load_bool_setting(USE_IGNORE_FILE_EXTENSIONS_KEY, False)
        self._ignore_file_extensions = self._load_list_setting(IGNORE_FILE_EXTENSIONS_KEY)
        self._use_only_search_file_extension = self._load_bool_setting(USE_ONLY_SEARCH_FILE_EXTENSION_KEY, False)
        self._only_search_file_extension = str(self._settings.value(ONLY_SEARCH_FILE_EXTENSION_KEY, "") or "")
        self._sort_field = "size"
        self._sort_direction = "descending"
        self._scan_summary: dict[str, object] = {
            "folder": self._selected_folder,
            "currentPath": self._selected_folder,
            "phase": "Idle",
            "totalFiles": 0,
            "totalFolders": 0,
            "skippedFiles": 0,
            "groupCount": 0,
            "duplicateFiles": 0,
            "hashCandidates": 0,
            "hashWorkCandidates": 0,
            "hashedFiles": 0,
            "hashCandidatesProcessed": 0,
            "hashBytesProcessed": 0,
            "hashTotalBytes": 0,
            "currentFileBytes": 0,
            "currentFileSize": 0,
            "wastedBytes": 0,
        }
        self._is_scanning = False
        self._is_cancelling = False
        self._scan_thread: QThread | None = None
        self._scan_worker: ScanWorker | None = None
        self._cleanup_worker = None
        self._cleanup_thread = None

    def _normalize_path(self, path: str) -> str:
        url = QUrl(path)
        if url.isLocalFile():
            path = url.toLocalFile()
        return str(Path(path).expanduser().absolute())

    @Slot(str, result=QUrl)
    def fileUrl(self, path: str) -> QUrl:
        return QUrl.fromLocalFile(self._normalize_path(path))

    @Slot()
    def shutdown(self) -> None:
        if self._scan_worker is not None:
            self._scan_worker.cancel()
        if self._scan_thread is not None:
            self._scan_thread.quit()
            self._scan_thread.wait()
        self._cleanup_scan()
        if self._cleanup_worker is not None:
            self._cleanup_worker.cancel()
        if self._cleanup_thread is not None:
            self._cleanup_thread.quit()
            self._cleanup_thread.wait()
        self._cleanup_worker = None
        self._cleanup_thread = None

    def get_is_cleaning(self) -> bool:
        return self._cleanup_thread is not None

    isCleaning = Property(bool, get_is_cleaning, notify=isCleaningChanged)

    @Slot()
    def stopCleanup(self) -> None:
        if self._cleanup_worker is not None:
            self._cleanup_worker.cancel()
            self.setStatusText("Cancelling cleanup…")

    def _load_recent_folders(self) -> list[str]:
        value = self._settings.value(RECENT_FOLDERS_KEY, [])
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [str(item) for item in value if str(item)]
        return []

    def _save_recent_folders(self) -> None:
        self._settings.setValue(RECENT_FOLDERS_KEY, self._recent_folders)

    def _load_bool_setting(self, key: str, default: bool) -> bool:
        value = self._settings.value(key, default)
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    def _load_int_setting(self, key: str, default: int) -> int:
        value = self._settings.value(key, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _load_list_setting(self, key: str) -> list[str]:
        value = self._settings.value(key, [])
        if isinstance(value, str):
            return [value] if value else []
        if isinstance(value, list):
            return [str(item) for item in value if str(item)]
        return []

    def _save_scan_preferences(self) -> None:
        self._settings.setValue(IGNORE_EMPTY_FILES_KEY, self._ignore_empty_files)
        self._settings.setValue(INCLUDE_SUBFOLDERS_KEY, self._include_subfolders)
        self._settings.setValue(LIMIT_FILE_SIZE_RANGE_KEY, self._limit_file_size_range)
        self._settings.setValue(MIN_FILE_SIZE_BYTES_KEY, self._min_file_size_bytes)
        self._settings.setValue(MAX_FILE_SIZE_BYTES_KEY, self._max_file_size_bytes)
        self._settings.setValue(USE_DUPLICATE_SEARCH_LIMIT_KEY, self._use_duplicate_search_limit)
        self._settings.setValue(DUPLICATE_SEARCH_LIMIT_KEY, self._duplicate_search_limit)
        self._settings.setValue(USE_IGNORE_FOLDER_PATTERNS_KEY, self._use_ignore_folder_patterns)
        self._settings.setValue(IGNORE_FOLDER_PATTERNS_KEY, self._ignore_folder_patterns)
        self._settings.setValue(USE_IGNORE_FILE_EXTENSIONS_KEY, self._use_ignore_file_extensions)
        self._settings.setValue(IGNORE_FILE_EXTENSIONS_KEY, self._ignore_file_extensions)
        self._settings.setValue(USE_ONLY_SEARCH_FILE_EXTENSION_KEY, self._use_only_search_file_extension)
        self._settings.setValue(ONLY_SEARCH_FILE_EXTENSION_KEY, self._only_search_file_extension)

    def _parse_size_text(self, value: str, *, default: int) -> int | None:
        cleaned = value.strip().upper().replace(" ", "")
        if not cleaned:
            return default

        multiplier = 1
        if cleaned.endswith("GB"):
            multiplier = 1024 * 1024 * 1024
            cleaned = cleaned[:-2]
        elif cleaned.endswith("MB"):
            multiplier = 1024 * 1024
            cleaned = cleaned[:-2]
        elif cleaned.endswith("KB"):
            multiplier = 1024
            cleaned = cleaned[:-2]
        elif cleaned.endswith("B"):
            cleaned = cleaned[:-1]

        try:
            numeric = float(cleaned)
        except ValueError:
            return None

        if not math.isfinite(numeric) or numeric < 0 or numeric * multiplier > 2**53:
            return None
        return int(numeric * multiplier)

    def _record_recent_folder(self, folder: str) -> None:
        normalized = self._normalize_path(folder)
        self._recent_folders = [path for path in self._recent_folders if path != normalized]
        self._recent_folders.insert(0, normalized)
        self._recent_folders = self._recent_folders[:MAX_RECENT_FOLDERS]
        self._save_recent_folders()
        self.recentFoldersChanged.emit()

    def _reset_scan_summary(self, folder: str, phase: str) -> None:
        self._scan_summary = {
            "folder": folder,
            "currentPath": folder,
            "phase": phase,
            "totalFiles": 0,
            "totalFolders": 0,
            "skippedFiles": 0,
            "groupCount": 0,
            "duplicateFiles": 0,
            "hashCandidates": 0,
            "hashWorkCandidates": 0,
            "hashedFiles": 0,
            "hashCandidatesProcessed": 0,
            "hashBytesProcessed": 0,
            "hashTotalBytes": 0,
            "currentFileBytes": 0,
            "currentFileSize": 0,
            "wastedBytes": 0,
        }
        self.scanSummaryChanged.emit()

    def _build_empty_preview(self) -> dict[str, object]:
        return {
            "path": "",
            "name": "No file selected",
            "suffix": "",
            "sizeBytes": 0,
            "fileHash": "",
            "previewKind": "none",
            "previewUrl": "",
            "textContent": "Select a file from the duplicate results to preview it here.",
            "statusText": "",
            "isTruncated": False,
            "isDeleted": False,
        }

    def _set_preview_data(self, data: dict[str, object]) -> None:
        self._preview_data = data
        self.previewDataChanged.emit()

    def _sort_duplicate_groups(self) -> None:
        reverse = self._sort_direction == "descending"

        def metric(group: dict[str, object]) -> int:
            if self._sort_field == "count":
                return int(group.get("count", 0))
            return int(group.get("sizeBytes", 0))

        def sort_key(group: dict[str, object]) -> tuple[bool, int, int, int]:
            files = [str(path) for path in group.get("files", [])]
            remaining = sum(1 for file_path in files if file_path not in self._deleted_paths)
            demote = remaining <= 1
            primary = metric(group)
            secondary = int(group.get("wastedBytes", 0))
            tertiary = int(group.get("count", 0))
            if reverse:
                return (demote, -primary, -secondary, -tertiary)
            return (demote, primary, secondary, tertiary)

        self._duplicate_groups.sort(key=sort_key)

    def _clear_deleted_paths(self) -> None:
        if not self._deleted_paths:
            return
        self._deleted_paths = []
        self.deletedPathsChanged.emit()
        self.magicCleanupChanged.emit()

    def _levenshtein_distance_with_limit(self, left: str, right: str, limit: int) -> int:
        if left == right:
            return 0
        if abs(len(left) - len(right)) > limit:
            return limit + 1
        previous = list(range(len(right) + 1))
        for i, left_char in enumerate(left, start=1):
            current = [i]
            row_min = current[0]
            for j, right_char in enumerate(right, start=1):
                cost = 0 if left_char == right_char else 1
                current_value = min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + cost,
                )
                current.append(current_value)
                row_min = min(row_min, current_value)
            if row_min > limit:
                return limit + 1
            previous = current
        return previous[-1]

    def _collect_magic_cleanup_candidates(self) -> list[str]:
        candidates: list[str] = []
        seen: set[str] = set()
        for group in self._duplicate_groups:
            active_files: list[Path] = []
            for file_value in group.get("files", []):
                normalized = self._normalize_path(str(file_value))
                if normalized in self._deleted_paths or normalized in seen:
                    continue
                path = Path(normalized)
                if path.exists() and path.is_file():
                    active_files.append(path)
            folders: dict[Path, list[Path]] = {}
            for file_path in active_files:
                folders.setdefault(file_path.parent, []).append(file_path)
            for folder_paths in folders.values():
                if len(folder_paths) < 2:
                    continue
                try:
                    ordered = sorted(folder_paths, key=lambda p: (p.stat().st_mtime_ns, p.name.lower()))
                except OSError:
                    continue
                retained = ordered[0]
                retained_name = retained.stem.lower()
                for candidate in ordered[1:]:
                    distance = self._levenshtein_distance_with_limit(retained_name, candidate.stem.lower(), 3)
                    if distance < 4:
                        normalized_candidate = str(candidate)
                        if normalized_candidate not in seen:
                            seen.add(normalized_candidate)
                            candidates.append(normalized_candidate)
        return candidates

    def get_selected_folder(self) -> str:
        return self._selected_folder

    @Slot(str)
    def setSelectedFolder(self, folder: str) -> None:
        if self._is_scanning or self.get_is_cleaning():
            return
        normalized = self._normalize_path(folder)
        if normalized == self._selected_folder:
            return

        self._selected_folder = normalized
        self.selectedFolderChanged.emit()
        self._duplicate_groups = []
        self.duplicateGroupsChanged.emit()
        self.magicCleanupChanged.emit()
        self._clear_deleted_paths()
        self._set_preview_data(self._build_empty_preview())
        self._reset_scan_summary(normalized, "Ready")
        self.setStatusText(f"Ready to scan: {normalized}")

    selectedFolder = Property(str, get_selected_folder, notify=selectedFolderChanged)

    def get_recent_folders(self) -> list[str]:
        return self._recent_folders

    recentFolders = Property("QVariantList", get_recent_folders, notify=recentFoldersChanged)

    def get_sort_field(self) -> str:
        return self._sort_field

    @Slot(str)
    def setSortField(self, value: str) -> None:
        if value not in {"size", "count"} or value == self._sort_field:
            return
        self._sort_field = value
        self.sortFieldChanged.emit()
        self._sort_duplicate_groups()
        self.duplicateGroupsChanged.emit()
        self.magicCleanupChanged.emit()

    sortField = Property(str, get_sort_field, notify=sortFieldChanged)

    def get_sort_direction(self) -> str:
        return self._sort_direction

    @Slot(str)
    def setSortDirection(self, value: str) -> None:
        if value not in {"ascending", "descending"} or value == self._sort_direction:
            return
        self._sort_direction = value
        self.sortDirectionChanged.emit()
        self._sort_duplicate_groups()
        self.duplicateGroupsChanged.emit()
        self.magicCleanupChanged.emit()

    sortDirection = Property(str, get_sort_direction, notify=sortDirectionChanged)

    def get_ignore_empty_files(self) -> bool:
        return self._ignore_empty_files

    @Slot(bool)
    def setIgnoreEmptyFiles(self, value: bool) -> None:
        if self._ignore_empty_files == value:
            return
        self._ignore_empty_files = value
        self._save_scan_preferences()
        self.ignoreEmptyFilesChanged.emit()

    ignoreEmptyFiles = Property(bool, get_ignore_empty_files, notify=ignoreEmptyFilesChanged)

    def get_include_subfolders(self) -> bool:
        return self._include_subfolders

    @Slot(bool)
    def setIncludeSubfolders(self, value: bool) -> None:
        if self._include_subfolders == value:
            return
        self._include_subfolders = value
        self._save_scan_preferences()
        self.includeSubfoldersChanged.emit()

    includeSubfolders = Property(bool, get_include_subfolders, notify=includeSubfoldersChanged)

    def get_limit_file_size_range(self) -> bool:
        return self._limit_file_size_range

    @Slot(bool)
    def setLimitFileSizeRange(self, value: bool) -> None:
        if self._limit_file_size_range == value:
            return
        self._limit_file_size_range = value
        self._save_scan_preferences()
        self.limitFileSizeRangeChanged.emit()

    limitFileSizeRange = Property(bool, get_limit_file_size_range, notify=limitFileSizeRangeChanged)

    def get_min_file_size_bytes(self) -> int:
        return self._min_file_size_bytes

    @Slot(str)
    def setMinFileSizeText(self, value: str) -> None:
        new_value = self._parse_size_text(value, default=DEFAULT_MIN_FILE_SIZE_BYTES)
        if new_value is None or new_value == self._min_file_size_bytes:
            return

        self._min_file_size_bytes = new_value
        self._save_scan_preferences()
        self.minFileSizeBytesChanged.emit()

    minFileSizeBytes = Property("qlonglong", get_min_file_size_bytes, notify=minFileSizeBytesChanged)

    def get_max_file_size_bytes(self) -> int:
        return self._max_file_size_bytes

    @Slot(str)
    def setMaxFileSizeText(self, value: str) -> None:
        new_value = self._parse_size_text(value, default=DEFAULT_MAX_FILE_SIZE_BYTES)
        if new_value is None or new_value == self._max_file_size_bytes:
            return

        self._max_file_size_bytes = new_value
        self._save_scan_preferences()
        self.maxFileSizeBytesChanged.emit()

    maxFileSizeBytes = Property("qlonglong", get_max_file_size_bytes, notify=maxFileSizeBytesChanged)

    def get_use_duplicate_search_limit(self) -> bool:
        return self._use_duplicate_search_limit

    @Slot(bool)
    def setUseDuplicateSearchLimit(self, value: bool) -> None:
        if self._use_duplicate_search_limit == value:
            return
        self._use_duplicate_search_limit = value
        self._save_scan_preferences()
        self.useDuplicateSearchLimitChanged.emit()

    useDuplicateSearchLimit = Property(bool, get_use_duplicate_search_limit, notify=useDuplicateSearchLimitChanged)

    def get_duplicate_search_limit(self) -> int:
        return self._duplicate_search_limit

    @Slot(str)
    def setDuplicateSearchLimitText(self, value: str) -> None:
        try:
            new_value = max(1, int(value.strip() or DEFAULT_DUPLICATE_SEARCH_LIMIT))
        except ValueError:
            return
        if new_value == self._duplicate_search_limit:
            return
        self._duplicate_search_limit = new_value
        self._save_scan_preferences()
        self.duplicateSearchLimitChanged.emit()

    duplicateSearchLimit = Property(int, get_duplicate_search_limit, notify=duplicateSearchLimitChanged)

    def get_use_ignore_folder_patterns(self) -> bool:
        return self._use_ignore_folder_patterns

    @Slot(bool)
    def setUseIgnoreFolderPatterns(self, value: bool) -> None:
        if self._use_ignore_folder_patterns == value:
            return
        self._use_ignore_folder_patterns = value
        self._save_scan_preferences()
        self.useIgnoreFolderPatternsChanged.emit()

    useIgnoreFolderPatterns = Property(bool, get_use_ignore_folder_patterns, notify=useIgnoreFolderPatternsChanged)

    def get_ignore_folder_patterns(self) -> list[str]:
        return self._ignore_folder_patterns

    ignoreFolderPatterns = Property("QVariantList", get_ignore_folder_patterns, notify=ignoreFolderPatternsChanged)

    @Slot(str)
    def addIgnoreFolderPattern(self, value: str) -> None:
        pattern = value.strip()
        if not pattern:
            return
        try:
            re.compile(pattern)
        except re.error as exc:
            self.setStatusText(f"Invalid folder regex: {exc}")
            return
        if pattern in self._ignore_folder_patterns:
            return
        self._ignore_folder_patterns = [*self._ignore_folder_patterns, pattern]
        self._save_scan_preferences()
        self.ignoreFolderPatternsChanged.emit()

    @Slot(str)
    def removeIgnoreFolderPattern(self, value: str) -> None:
        if value not in self._ignore_folder_patterns:
            return
        self._ignore_folder_patterns = [item for item in self._ignore_folder_patterns if item != value]
        self._save_scan_preferences()
        self.ignoreFolderPatternsChanged.emit()

    def get_use_ignore_file_extensions(self) -> bool:
        return self._use_ignore_file_extensions

    @Slot(bool)
    def setUseIgnoreFileExtensions(self, value: bool) -> None:
        if self._use_ignore_file_extensions == value:
            return
        self._use_ignore_file_extensions = value
        self._save_scan_preferences()
        self.useIgnoreFileExtensionsChanged.emit()

    useIgnoreFileExtensions = Property(bool, get_use_ignore_file_extensions, notify=useIgnoreFileExtensionsChanged)

    def get_ignore_file_extensions(self) -> list[str]:
        return self._ignore_file_extensions

    ignoreFileExtensions = Property("QVariantList", get_ignore_file_extensions, notify=ignoreFileExtensionsChanged)

    @Slot(str)
    def addIgnoreFileExtension(self, value: str) -> None:
        extension = value.strip().lower()
        if not extension:
            return
        if not extension.startswith("."):
            extension = "." + extension
        if extension in self._ignore_file_extensions:
            return
        self._ignore_file_extensions = [*self._ignore_file_extensions, extension]
        self._save_scan_preferences()
        self.ignoreFileExtensionsChanged.emit()

    @Slot(str)
    def removeIgnoreFileExtension(self, value: str) -> None:
        extension = value.strip().lower()
        if not extension.startswith(".") and extension:
            extension = "." + extension
        if extension not in self._ignore_file_extensions:
            return
        self._ignore_file_extensions = [item for item in self._ignore_file_extensions if item != extension]
        self._save_scan_preferences()
        self.ignoreFileExtensionsChanged.emit()

    def get_use_only_search_file_extension(self) -> bool:
        return self._use_only_search_file_extension

    @Slot(bool)
    def setUseOnlySearchFileExtension(self, value: bool) -> None:
        if self._use_only_search_file_extension == value:
            return
        self._use_only_search_file_extension = value
        self._save_scan_preferences()
        self.useOnlySearchFileExtensionChanged.emit()

    useOnlySearchFileExtension = Property(bool, get_use_only_search_file_extension, notify=useOnlySearchFileExtensionChanged)

    def get_only_search_file_extension(self) -> str:
        return self._only_search_file_extension

    @Slot(str)
    def setOnlySearchFileExtensionText(self, value: str) -> None:
        extension = value.strip().lower()
        if extension and not extension.startswith("."):
            extension = "." + extension
        if extension == self._only_search_file_extension:
            return
        self._only_search_file_extension = extension
        self._save_scan_preferences()
        self.onlySearchFileExtensionChanged.emit()

    onlySearchFileExtension = Property(str, get_only_search_file_extension, notify=onlySearchFileExtensionChanged)

    def get_deleted_paths(self) -> list[str]:
        return self._deleted_paths

    deletedPaths = Property("QVariantList", get_deleted_paths, notify=deletedPathsChanged)

    def get_preview_data(self) -> dict[str, object]:
        return self._preview_data

    previewData = Property("QVariantMap", get_preview_data, notify=previewDataChanged)

    def get_status_text(self) -> str:
        return self._status_text

    @Slot(str)
    def setStatusText(self, text: str) -> None:
        if text == self._status_text:
            return
        self._status_text = text
        self.statusTextChanged.emit()

    statusText = Property(str, get_status_text, notify=statusTextChanged)

    def get_duplicate_groups(self) -> list[dict[str, object]]:
        return self._duplicate_groups

    duplicateGroups = Property("QVariantList", get_duplicate_groups, notify=duplicateGroupsChanged)

    def get_scan_summary(self) -> dict[str, object]:
        return self._scan_summary

    scanSummary = Property("QVariantMap", get_scan_summary, notify=scanSummaryChanged)

    def get_is_scanning(self) -> bool:
        return self._is_scanning

    isScanning = Property(bool, get_is_scanning, notify=isScanningChanged)

    def _set_is_scanning(self, value: bool) -> None:
        if self._is_scanning == value:
            return
        self._is_scanning = value
        self.isScanningChanged.emit()

    def get_is_cancelling(self) -> bool:
        return self._is_cancelling

    isCancelling = Property(bool, get_is_cancelling, notify=isCancellingChanged)

    def _set_is_cancelling(self, value: bool) -> None:
        if self._is_cancelling == value:
            return
        self._is_cancelling = value
        self.isCancellingChanged.emit()

    def _cleanup_scan(self) -> None:
        self._scan_worker = None
        self._scan_thread = None
        self._set_is_cancelling(False)
        self._set_is_scanning(False)

    @Slot(str, result=bool)
    def isDeletedPath(self, path: str) -> bool:
        return self._normalize_path(path) in self._deleted_paths

    @Slot(str)
    def selectPreviewFile(self, path: str) -> None:
        normalized = self._normalize_path(path)
        file_path = Path(normalized)
        if not file_path.exists() or not file_path.is_file():
            self._set_preview_data(
                {
                    **self._build_empty_preview(),
                    "path": str(file_path),
                    "name": file_path.name or str(file_path),
                    "statusText": "File is no longer available.",
                    "isDeleted": normalized in self._deleted_paths,
                }
            )
            return

        try:
            size_bytes = file_path.stat().st_size
        except OSError:
            size_bytes = 0

        suffix = file_path.suffix.lower()
        preview = {
            "path": str(file_path),
            "name": file_path.name,
            "suffix": suffix,
            "sizeBytes": size_bytes,
            "fileHash": "",
            "previewKind": "none",
            "previewUrl": "",
            "textContent": "",
            "statusText": "Preview not available for this file type.",
            "isTruncated": False,
            "isDeleted": normalized in self._deleted_paths,
        }

        # Reuse scan evidence instead of hashing gigabytes on the GUI thread.
        preview["fileHash"] = "Not available; scan this file first."
        for group in self._duplicate_groups:
            if normalized in group.get("files", []):
                try:
                    unchanged = fingerprint(file_path) == tuple(group.get("snapshots", {}).get(normalized, ()))
                except OSError:
                    unchanged = False
                preview["fileHash"] = group.get("hash", "") if unchanged else "File changed; scan again."
                break

        if suffix in IMAGE_SUFFIXES:
            preview.update(
                {
                    "previewKind": "image",
                    "previewUrl": file_path.resolve().as_uri(),
                    "statusText": "Image preview",
                }
            )
        elif suffix in PDF_SUFFIXES:
            preview.update(
                {
                    "previewKind": "pdf",
                    "previewUrl": file_path.resolve().as_uri(),
                    "statusText": "PDF preview",
                }
            )
        elif suffix in TEXT_SUFFIXES or size_bytes <= MAX_TEXT_PREVIEW_BYTES:
            try:
                with file_path.open("rb") as stream:
                    raw_text = stream.read(MAX_TEXT_PREVIEW_BYTES + 1)
            except OSError:
                preview["statusText"] = "Could not read this file for preview."
            else:
                preview.update(
                    {
                        "previewKind": "text",
                        "textContent": raw_text[:MAX_TEXT_PREVIEW_BYTES].decode("utf-8", errors="replace"),
                        "isTruncated": len(raw_text) > MAX_TEXT_PREVIEW_BYTES,
                        "statusText": "Text preview",
                    }
                )
        self._set_preview_data(preview)

    @Slot()
    def openPreviewFolder(self) -> None:
        path = self._preview_data.get("path", "")
        if path:
            self.showInFolder(path)

    @Slot(str)
    def showInFolder(self, path: str) -> None:
        normalized = self._normalize_path(path)
        folder = Path(normalized).parent
        if not folder.exists():
            self.setStatusText(f"Folder is no longer available: {folder}")
            return

        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder))):
            self.setStatusText(f"Could not open folder: {folder}")

    @Slot(str)
    def _record_removed(self, normalized: str) -> None:
        self._deleted_paths.append(normalized)
        if self._preview_data.get("path") == normalized:
            self._set_preview_data(
                {
                    **self._preview_data,
                    "previewKind": "none",
                    "previewUrl": "",
                    "statusText": "Moved to Trash / Recycle Bin.",
                    "textContent": "Restore this file using your system's Trash / Recycle Bin.",
                    "isDeleted": True,
                }
            )
        self.deletedPathsChanged.emit()
        self._refresh_remaining_summary()

    def _start_cleanup(self, paths: list[str]) -> None:
        if self._is_scanning or self.get_is_cleaning():
            self.setStatusText("Wait for the current operation to finish.")
            return
        self._cleanup_thread = QThread(self)
        self._cleanup_worker = CleanupWorker(paths, list(self._duplicate_groups), self._deleted_paths)
        self._cleanup_worker.moveToThread(self._cleanup_thread)
        self._cleanup_thread.started.connect(self._cleanup_worker.run)
        self._cleanup_worker.moved.connect(self._record_removed)
        self._cleanup_worker.progress.connect(self.setStatusText)
        self._cleanup_worker.finished.connect(self._finish_cleanup)
        self._cleanup_worker.finished.connect(self._cleanup_worker.deleteLater)
        self._cleanup_thread.finished.connect(self._cleanup_thread.deleteLater)
        self.isCleaningChanged.emit()
        self._cleanup_thread.start()

    @Slot(dict)
    def _finish_cleanup(self, result: dict) -> None:
        if self._cleanup_thread is not None:
            self._cleanup_thread.quit()
            self._cleanup_thread.wait()
        self._cleanup_worker = None
        self._cleanup_thread = None
        self._sort_duplicate_groups()
        self.duplicateGroupsChanged.emit()
        self.magicCleanupChanged.emit()
        prefix = "Cleanup cancelled. " if result["cancelled"] else ""
        message = f"{prefix}Moved {result['removed']} files to Trash / Recycle Bin."
        if result["errors"]:
            message += f" {len(result['errors'])} skipped. {result['errors'][0]}"
        self.setStatusText(message)
        self.isCleaningChanged.emit()

    def get_magic_cleanup_candidate_count(self) -> int:
        return len(self._collect_magic_cleanup_candidates())

    magicCleanupCandidateCount = Property(int, get_magic_cleanup_candidate_count, notify=magicCleanupChanged)

    @Slot()
    def applyMagicCleanup(self) -> None:
        candidates = self._collect_magic_cleanup_candidates()
        if not candidates:
            self.setStatusText("No smart cleanup candidates found.")
            return

        self._start_cleanup(candidates)

    @Slot(str)
    def deleteFile(self, path: str) -> None:
        normalized = self._normalize_path(path)
        self._start_cleanup([normalized])

    def _refresh_remaining_summary(self) -> None:
        counts = [(g, sum(p not in self._deleted_paths for p in g["files"])) for g in self._duplicate_groups]
        active = [(g, n) for g, n in counts if n > 1]
        self._scan_summary.update(
            groupCount=len(active), duplicateFiles=sum(n for _, n in active),
            wastedBytes=sum(int(g["sizeBytes"]) * (n - 1) for g, n in active),
        )
        self.scanSummaryChanged.emit()

    @Slot(dict)
    def _update_scan_progress(self, progress: dict[str, object]) -> None:
        self._scan_summary = {
            **self._scan_summary,
            "folder": self._selected_folder,
            "currentPath": progress["currentPath"],
            "phase": progress["phase"],
            "totalFiles": progress["totalFiles"],
            "totalFolders": progress["totalFolders"],
            "skippedFiles": progress["skippedFiles"],
            "groupCount": progress["liveGroupCount"],
            "duplicateFiles": progress["liveDuplicateFiles"],
            "hashCandidates": progress["hashCandidates"],
            "hashWorkCandidates": progress["hashWorkCandidates"],
            "hashedFiles": progress["hashedFiles"],
            "hashCandidatesProcessed": progress["hashCandidatesProcessed"],
            "hashBytesProcessed": progress["hashBytesProcessed"],
            "hashTotalBytes": progress["hashTotalBytes"],
            "currentFileBytes": progress["currentFileBytes"],
            "currentFileSize": progress["currentFileSize"],
        }
        self.scanSummaryChanged.emit()

        if progress["hashCandidates"]:
            work_candidates = progress["hashWorkCandidates"]
            status = (
                f"Comparing file contents: {progress['hashCandidatesProcessed']} of "
                f"{work_candidates} candidates checked, "
                f"{_format_byte_count(progress['hashBytesProcessed'] + progress['currentFileBytes'])} of "
                f"{_format_byte_count(progress['hashTotalBytes'])} candidate bytes read; "
                f"{progress['skippedFiles']} skipped."
            )
        else:
            status = (
                f"Finding candidates: {progress['totalFiles']} eligible files checked across "
                f"{progress['totalFolders']} folders; {progress['skippedFiles']} skipped."
            )
        if progress["liveGroupCount"]:
            status += (
                f" Found {progress['liveGroupCount']} groups / "
                f"{progress['liveDuplicateFiles']} duplicate files."
            )
        self.setStatusText(status)

    @Slot(dict)
    def _complete_scan(self, results: dict[str, object]) -> None:
        self._duplicate_groups = results["groups"]
        self._sort_duplicate_groups()
        self.duplicateGroupsChanged.emit()
        self.magicCleanupChanged.emit()
        self._scan_summary = {
            "folder": results["folder"],
            "currentPath": results["currentPath"],
            "phase": "Stopped" if results["cancelled"] else ("Limited" if results.get("searchLimitReached") else "Complete"),
            "totalFiles": results["totalFiles"],
            "totalFolders": results["totalFolders"],
            "skippedFiles": results["skippedFiles"],
            "groupCount": results["groupCount"],
            "duplicateFiles": results["duplicateFiles"],
            "hashCandidates": self._scan_summary.get("hashCandidates", 0),
            "hashWorkCandidates": self._scan_summary.get("hashWorkCandidates", 0),
            "hashedFiles": self._scan_summary.get("hashedFiles", 0),
            "hashCandidatesProcessed": self._scan_summary.get("hashCandidatesProcessed", 0),
            "hashBytesProcessed": self._scan_summary.get("hashBytesProcessed", 0),
            "hashTotalBytes": self._scan_summary.get("hashTotalBytes", 0),
            "currentFileBytes": 0,
            "currentFileSize": 0,
            "wastedBytes": results["wastedBytes"],
        }
        self.scanSummaryChanged.emit()

        if results["cancelled"]:
            if results["groupCount"]:
                self.setStatusText(
                    "Scan stopped. Showing partial results: "
                    f"{results['groupCount']} groups from {results['totalFiles']} files across "
                    f"{results['totalFolders']} folders, with {results['skippedFiles']} skipped."
                )
            else:
                self.setStatusText(
                    "Scan stopped. "
                    f"Visited {results['totalFiles']} files across {results['totalFolders']} folders, "
                    f"skipped {results['skippedFiles']}."
                )
        elif results["groupCount"]:
            if results.get("searchLimitReached"):
                self.setStatusText(
                    "Duplicate search limit reached. Found "
                    f"{results['groupCount']} groups after scanning {results['totalFiles']} files "
                    f"in {results['totalFolders']} folders with {results['skippedFiles']} skipped."
                )
            else:
                self.setStatusText(
                    "Found "
                    f"{results['groupCount']} duplicate groups after scanning "
                    f"{results['totalFiles']} files in {results['totalFolders']} folders "
                    f"with {results['skippedFiles']} skipped."
                )
        elif results.get("searchLimitReached"):
            self.setStatusText("Search limit reached. No duplicates found in the checked subset; increase the limit for a complete scan.")
        else:
            self.setStatusText(
                f"No duplicates found in {results['totalFiles']} files across "
                f"{results['totalFolders']} folders. Skipped {results['skippedFiles']} unreadable files."
            )

        if self._scan_thread is not None:
            self._scan_thread.quit()
            self._scan_thread.wait()
        self._cleanup_scan()

    @Slot(str)
    def _fail_scan(self, message: str) -> None:
        self._scan_summary["phase"] = "Failed"
        self.scanSummaryChanged.emit()
        self.setStatusText(f"Scan failed: {message}")
        if self._scan_thread is not None:
            self._scan_thread.quit()
            self._scan_thread.wait()
        self._cleanup_scan()

    @Slot()
    def startScan(self) -> None:
        if self.get_is_cleaning():
            self.setStatusText("Wait for cleanup to finish.")
            return
        if self._is_scanning:
            self.stopScan()
            return

        folder = Path(self._selected_folder).expanduser()
        if not folder.exists():
            self.setStatusText(f"Folder does not exist: {folder}")
            return

        if not folder.is_dir():
            self.setStatusText(f"Selected path is not a folder: {folder}")
            return

        self._record_recent_folder(str(folder))
        self._duplicate_groups = []
        self.duplicateGroupsChanged.emit()
        self._clear_deleted_paths()
        self._set_preview_data(self._build_empty_preview())
        self._reset_scan_summary(str(folder), "Starting")
        self.setStatusText(f"Starting scan in {folder}...")

        self._scan_thread = QThread(self)
        min_file_size_bytes = min(self._min_file_size_bytes, self._max_file_size_bytes)
        max_file_size_bytes = max(self._min_file_size_bytes, self._max_file_size_bytes)
        self._scan_worker = ScanWorker(
            str(folder),
            ignore_empty_files=self._ignore_empty_files,
            include_subfolders=self._include_subfolders,
            limit_file_size_range=self._limit_file_size_range,
            min_file_size_bytes=min_file_size_bytes,
            max_file_size_bytes=max_file_size_bytes,
            use_duplicate_search_limit=self._use_duplicate_search_limit,
            duplicate_search_limit=self._duplicate_search_limit,
            use_ignore_folder_patterns=self._use_ignore_folder_patterns,
            ignore_folder_patterns=self._ignore_folder_patterns,
            use_ignore_file_extensions=self._use_ignore_file_extensions,
            ignore_file_extensions=self._ignore_file_extensions,
            use_only_search_file_extension=self._use_only_search_file_extension,
            only_search_file_extension=self._only_search_file_extension,
        )
        self._scan_worker.moveToThread(self._scan_thread)
        self._scan_thread.started.connect(self._scan_worker.run)
        self._scan_worker.progress.connect(self._update_scan_progress)
        self._scan_worker.finished.connect(self._complete_scan)
        self._scan_worker.failed.connect(self._fail_scan)
        self._scan_worker.finished.connect(self._scan_worker.deleteLater)
        self._scan_worker.failed.connect(self._scan_worker.deleteLater)
        self._scan_thread.finished.connect(self._scan_thread.deleteLater)
        self._set_is_cancelling(False)
        self._set_is_scanning(True)
        self._scan_thread.start()

    @Slot()
    def stopScan(self) -> None:
        if not self._is_scanning or self._scan_worker is None:
            return

        self._set_is_cancelling(True)
        self.setStatusText(
            f"Cancelling... {self._scan_summary['totalFiles']} files and "
            f"{self._scan_summary['totalFolders']} folders scanned so far."
        )
        self._scan_worker.cancel()
