"""Expose wheel gesture phases that Qt Quick's WheelEvent omits."""
import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication, QInputDevice
from PySide6.QtQml import QmlElement
from PySide6.QtQuick import QQuickItem

QML_IMPORT_NAME = "DuplicateCleaner.Input"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class ScrollWheelArea(QQuickItem):
    scrolled = Signal(float, int, float, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

    def wheelEvent(self, event):
        pixels = event.pixelDelta()
        angles = event.angleDelta()
        if event.modifiers() != Qt.KeyboardModifier.NoModifier or (
            (pixels.x() and not pixels.y()) or (angles.x() and not angles.y())
        ):
            event.ignore()
            return
        phase = event.phase()
        precise = (
            not pixels.isNull()
            or event.device().type() == QInputDevice.DeviceType.TouchPad
            or phase != Qt.ScrollPhase.NoScrollPhase
        )
        # Values retain the platform's natural-scroll direction.
        distance = -pixels.y() if not pixels.isNull() else (
            -angles.y() / 120 * QGuiApplication.styleHints().wheelScrollLines() * 24
        )
        self.scrolled.emit(distance, phase.value, event.timestamp() or time.monotonic() * 1000, precise)
        event.accept()
