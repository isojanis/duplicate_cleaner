from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QLibraryInfo
from PySide6.QtCore import QLibraryInfo
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from .bridge import AppBridge


SYSTEM_QML_IMPORT_PATHS = (
    "/usr/lib64/qt6/qml",
    "/usr/lib/qt6/qml",
    "/usr/local/lib64/qt6/qml",
    "/usr/local/lib/qt6/qml",
)


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Duplicate Cleaner")
    app.setOrganizationName("isojanis")
    app.setDesktopFileName("duplicate-cleaner")

    qml_path = Path(__file__).resolve().parents[2] / "qml" / "Main.qml"

    engine = QQmlApplicationEngine()

    # PySide wheels may not include distro QML paths, so add common Linux Qt6 import roots.
    qt_qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.QmlImportsPath)
    if qt_qml_path:
        engine.addImportPath(qt_qml_path)

    for import_path in SYSTEM_QML_IMPORT_PATHS:
        if Path(import_path).exists():
            engine.addImportPath(import_path)

    bridge = AppBridge()
    engine.rootContext().setContextProperty("appBridge", bridge)
    engine.load(str(qml_path))

    if not engine.rootObjects():
        return 1

    return app.exec()
