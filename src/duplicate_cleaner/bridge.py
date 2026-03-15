from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import subprocess

from PySide6.QtCore import QObject, Property, QSettings, QThread, Signal, Slot

from .scanner import scan_for_duplicates

RECENT_FOLDERS_KEY = "recentFolders"
MAX_RECENT_FOLDERS = 10
MAX_TEXT_PREVIEW_BYTES = 100_000
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"}
PDF_SUFFIXES = {".pdf"}
TEXT_SUFFIXES = {
    ".txt", ".md", ".py", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".log", ".csv", ".qml", ".js", ".ts", ".html", ".htm", ".css", ".xml",
    ".sh", ".bash", ".zsh", ".c", ".cc", ".cpp", ".h", ".hpp", ".rs", ".java",
}


class ScanWorker(QObject):
    progress = Signal(dict)
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, folder: str) -> None:
        super().__init__()
        self._folder = Path(folder).expanduser()
        self._cancel_requested = False

    @Slot()
    def run(self) -> None:
        try:
            results = scan_for_duplicates(
                self._folder,
                progress_callback=self.progress.emit,
                should_cancel=lambda: self._cancel_requested,
            )
        except Exception as exc:  # pragma: no cover - defensive bridge layer
            self.failed.emit(str(exc))
            return

        self.finished.emit(results)

    @Slot()
    def cancel(self) -> None:
        self._cancel_requested = True


class AppBridge(QObject):
    selectedFolderChanged = Signal()
    recentFoldersChanged = Signal()
    previewDataChanged = Signal()
    statusTextChanged = Signal()
    duplicateGroupsChanged = Signal()
    scanSummaryChanged = Signal()
    isScanningChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._settings = QSettings()
        self._recent_folders = self._load_recent_folders()
        self._selected_folder = self._recent_folders[0] if self._recent_folders else str(Path.home())
        self._status_text = "Choose a folder to begin."
        self._duplicate_groups: list[dict[str, object]] = []
        self._preview_data = self._build_empty_preview()
        self._scan_summary: dict[str, object] = {
            "folder": self._selected_folder,
            "currentPath": self._selected_folder,
            "phase": "Idle",
            "totalFiles": 0,
            "totalFolders": 0,
            "skippedFiles": 0,
            "groupCount": 0,
            "duplicateFiles": 0,
            "liveGroupCount": 0,
            "liveDuplicateFiles": 0,
            "hashCandidates": 0,
            "hashedFiles": 0,
            "wastedBytes": 0,
        }
        self._is_scanning = False
        self._scan_thread: QThread | None = None
        self._scan_worker: ScanWorker | None = None

    def _load_recent_folders(self) -> list[str]:
        value = self._settings.value(RECENT_FOLDERS_KEY, [])
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [str(item) for item in value if str(item)]
        return []

    def _save_recent_folders(self) -> None:
        self._settings.setValue(RECENT_FOLDERS_KEY, self._recent_folders)

    def _record_recent_folder(self, folder: str) -> None:
        normalized = str(Path(folder).expanduser())
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
            "liveGroupCount": 0,
            "liveDuplicateFiles": 0,
            "hashCandidates": 0,
            "hashedFiles": 0,
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
        }

    def _set_preview_data(self, data: dict[str, object]) -> None:
        self._preview_data = data
        self.previewDataChanged.emit()


    def _hash_file_for_preview(self, file_path: Path) -> str:
        digest = sha256()
        with file_path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
        return digest.hexdigest()

    def get_selected_folder(self) -> str:
        return self._selected_folder

    @Slot(str)
    def setSelectedFolder(self, folder: str) -> None:
        if folder.startswith("file://"):
            folder = folder.removeprefix("file://")

        normalized = str(Path(folder).expanduser())
        if normalized == self._selected_folder:
            return

        self._selected_folder = normalized
        self.selectedFolderChanged.emit()
        self._duplicate_groups = []
        self.duplicateGroupsChanged.emit()
        self._set_preview_data(self._build_empty_preview())
        self._reset_scan_summary(normalized, "Ready")
        self.setStatusText(f"Ready to scan: {normalized}")

    selectedFolder = Property(str, get_selected_folder, notify=selectedFolderChanged)

    def get_recent_folders(self) -> list[str]:
        return self._recent_folders

    recentFolders = Property("QVariantList", get_recent_folders, notify=recentFoldersChanged)

    def get_preview_data(self) -> dict[str, object]:
        return self._preview_data

    previewData = Property("QVariantMap", get_preview_data, notify=previewDataChanged)

    def get_status_text(self) -> str:
        return self._status_text

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

    def _cleanup_scan(self) -> None:
        self._scan_worker = None
        self._scan_thread = None
        self._set_is_scanning(False)

    @Slot(str)
    def selectPreviewFile(self, path: str) -> None:
        if path.startswith("file://"):
            path = path.removeprefix("file://")

        file_path = Path(path).expanduser()
        if not file_path.exists() or not file_path.is_file():
            self._set_preview_data(
                {
                    **self._build_empty_preview(),
                    "path": str(file_path),
                    "name": file_path.name or str(file_path),
                    "statusText": "File is no longer available.",
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
        }

        try:
            preview["fileHash"] = self._hash_file_for_preview(file_path)
        except OSError:
            preview["statusText"] = "Could not read this file to calculate a preview hash."
            self._set_preview_data(preview)
            return

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
                raw_text = file_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                preview["statusText"] = "Could not read this file for preview."
            else:
                preview.update(
                    {
                        "previewKind": "text",
                        "textContent": raw_text[:MAX_TEXT_PREVIEW_BYTES],
                        "isTruncated": len(raw_text) > MAX_TEXT_PREVIEW_BYTES,
                        "statusText": "Text preview",
                    }
                )
        self._set_preview_data(preview)

    @Slot()
    def openPreviewFolder(self) -> None:
        path = self._preview_data.get("path", "")
        if not path:
            return

        folder = Path(path).expanduser().parent
        if not folder.exists():
            self.setStatusText(f"Preview folder is no longer available: {folder}")
            return

        try:
            subprocess.Popen(["xdg-open", str(folder)])
        except OSError as exc:
            self.setStatusText(f"Could not open folder: {exc}")

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
            "liveGroupCount": progress["liveGroupCount"],
            "liveDuplicateFiles": progress["liveDuplicateFiles"],
            "hashCandidates": progress["hashCandidates"],
            "hashedFiles": progress["hashedFiles"],
        }
        self.scanSummaryChanged.emit()

        status = (
            f"{progress['phase']} {progress['totalFiles']} files, "
            f"{progress['totalFolders']} folders, {progress['skippedFiles']} skipped."
        )
        if progress["liveGroupCount"]:
            status += (
                f" Live duplicates: {progress['liveGroupCount']} groups / "
                f"{progress['liveDuplicateFiles']} files."
            )
        self.setStatusText(status)

    @Slot(dict)
    def _complete_scan(self, results: dict[str, object]) -> None:
        self._duplicate_groups = results["groups"]
        self._duplicate_groups.sort(key=lambda group: (group["wastedBytes"], group["count"]), reverse=True)
        self.duplicateGroupsChanged.emit()
        self._scan_summary = {
            "folder": results["folder"],
            "currentPath": results["currentPath"],
            "phase": "Stopped" if results["cancelled"] else "Complete",
            "totalFiles": results["totalFiles"],
            "totalFolders": results["totalFolders"],
            "skippedFiles": results["skippedFiles"],
            "groupCount": results["groupCount"],
            "duplicateFiles": results["duplicateFiles"],
            "liveGroupCount": results["groupCount"],
            "liveDuplicateFiles": results["duplicateFiles"],
            "hashCandidates": self._scan_summary.get("hashCandidates", 0),
            "hashedFiles": self._scan_summary.get("hashedFiles", 0),
            "wastedBytes": results["wastedBytes"],
        }
        self.scanSummaryChanged.emit()

        if results["cancelled"]:
            self.setStatusText(
                "Scan stopped. "
                f"Visited {results['totalFiles']} files across {results['totalFolders']} folders, "
                f"skipped {results['skippedFiles']}."
            )
        elif results["groupCount"]:
            self.setStatusText(
                "Found "
                f"{results['groupCount']} duplicate groups after scanning "
                f"{results['totalFiles']} files in {results['totalFolders']} folders "
                f"with {results['skippedFiles']} skipped."
            )
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
        self.setStatusText(f"Scan failed: {message}")
        if self._scan_thread is not None:
            self._scan_thread.quit()
            self._scan_thread.wait()
        self._cleanup_scan()

    @Slot()
    def startScan(self) -> None:
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
        self._set_preview_data(self._build_empty_preview())
        self._reset_scan_summary(str(folder), "Starting")
        self.setStatusText(f"Starting scan in {folder}...")

        self._scan_thread = QThread(self)
        self._scan_worker = ScanWorker(str(folder))
        self._scan_worker.moveToThread(self._scan_thread)
        self._scan_thread.started.connect(self._scan_worker.run)
        self._scan_worker.progress.connect(self._update_scan_progress)
        self._scan_worker.finished.connect(self._complete_scan)
        self._scan_worker.failed.connect(self._fail_scan)
        self._scan_worker.finished.connect(self._scan_worker.deleteLater)
        self._scan_worker.failed.connect(self._scan_worker.deleteLater)
        self._scan_thread.finished.connect(self._scan_thread.deleteLater)
        self._set_is_scanning(True)
        self._scan_thread.start()

    @Slot()
    def stopScan(self) -> None:
        if not self._is_scanning or self._scan_worker is None:
            return

        self.setStatusText(
            f"Stopping scan after {self._scan_summary['totalFiles']} files and "
            f"{self._scan_summary['totalFolders']} folders..."
        )
        self._scan_worker.cancel()
