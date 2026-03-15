from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from .bridge import AppBridge


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Duplicate Cleaner")
    app.setOrganizationName("isojanis")
    app.setDesktopFileName("duplicate-cleaner")

    qml_path = Path(__file__).resolve().parents[2] / "qml" / "Main.qml"

    engine = QQmlApplicationEngine()
    bridge = AppBridge()
    engine.rootContext().setContextProperty("appBridge", bridge)
    engine.load(str(qml_path))

    if not engine.rootObjects():
        return 1

    return app.exec()
