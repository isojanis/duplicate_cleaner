from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Property, Signal, Slot


class AppBridge(QObject):
    selectedFolderChanged = Signal()
    statusTextChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._selected_folder = str(Path.home())
        self._status_text = "Choose a folder to begin."

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

    @Slot()
    def startScan(self) -> None:
        self.setStatusText(
            f"Scan is not implemented yet. Selected folder: {self._selected_folder}"
        )
