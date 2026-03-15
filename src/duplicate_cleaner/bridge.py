from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Property, QThread, Signal, Slot

from .scanner import scan_for_duplicates


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
    statusTextChanged = Signal()
    duplicateGroupsChanged = Signal()
    scanSummaryChanged = Signal()
    isScanningChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._selected_folder = str(Path.home())
        self._status_text = "Choose a folder to begin."
        self._duplicate_groups: list[dict[str, object]] = []
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
        self._scan_summary = {
            "folder": normalized,
            "currentPath": normalized,
            "phase": "Ready",
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
        self.setStatusText(f"Ready to scan: {normalized}")

    selectedFolder = Property(
        str,
        get_selected_folder,
        notify=selectedFolderChanged,
    )

    def get_status_text(self) -> str:
        return self._status_text

    def setStatusText(self, text: str) -> None:
        if text == self._status_text:
            return
        self._status_text = text
        self.statusTextChanged.emit()

    statusText = Property(
        str,
        get_status_text,
        notify=statusTextChanged,
    )

    def get_duplicate_groups(self) -> list[dict[str, object]]:
        return self._duplicate_groups

    duplicateGroups = Property(
        "QVariantList",
        get_duplicate_groups,
        notify=duplicateGroupsChanged,
    )

    def get_scan_summary(self) -> dict[str, object]:
        return self._scan_summary

    scanSummary = Property(
        "QVariantMap",
        get_scan_summary,
        notify=scanSummaryChanged,
    )

    def get_is_scanning(self) -> bool:
        return self._is_scanning

    isScanning = Property(
        bool,
        get_is_scanning,
        notify=isScanningChanged,
    )

    def _set_is_scanning(self, value: bool) -> None:
        if self._is_scanning == value:
            return
        self._is_scanning = value
        self.isScanningChanged.emit()

    def _cleanup_scan(self) -> None:
        self._scan_worker = None
        self._scan_thread = None
        self._set_is_scanning(False)

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
        self._duplicate_groups.sort(
            key=lambda group: (group["wastedBytes"], group["count"]),
            reverse=True,
        )
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

        self._duplicate_groups = []
        self.duplicateGroupsChanged.emit()
        self._scan_summary = {
            "folder": str(folder),
            "currentPath": str(folder),
            "phase": "Starting",
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
