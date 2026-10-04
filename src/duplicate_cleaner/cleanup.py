"""Run potentially slow revalidation and OS trash operations off the GUI thread."""
from pathlib import Path
from threading import Event

from PySide6.QtCore import QFile, QObject, Signal, Slot

from .safety import validate_removal


class CleanupWorker(QObject):
    moved = Signal(str)
    progress = Signal(str)
    finished = Signal(dict)

    def __init__(self, paths, groups, deleted):
        super().__init__()
        self.paths = paths
        self.groups = {path: group for group in groups for path in group["files"]}
        self.deleted = list(deleted)
        self.cancelled = Event()

    def cancel(self):
        self.cancelled.set()

    @Slot()
    def run(self):
        removed = 0
        errors = []
        try:
            for index, value in enumerate(self.paths, 1):
                if self.cancelled.is_set():
                    break
                self.progress.emit(f"Checking duplicate {index} of {len(self.paths)}: {value}")
                try:
                    if value in self.deleted:
                        continue
                    group = self.groups.get(value)
                    if group is None:
                        raise ValueError("File is not in the current scan results.")
                    validate_removal(Path(value), group, self.deleted, self.cancelled.is_set)
                    if self.cancelled.is_set():
                        break
                    file = QFile(value)
                    if not file.moveToTrash():
                        raise OSError(file.errorString())
                    self.deleted.append(value)
                    removed += 1
                    self.moved.emit(value)
                except InterruptedError:
                    break
                except (ValueError, OSError) as exc:
                    errors.append(f"{value}: {exc}")
        except Exception as exc:
            errors.append(str(exc))
        finally:
            self.finished.emit({"removed": removed, "errors": errors, "cancelled": self.cancelled.is_set()})
