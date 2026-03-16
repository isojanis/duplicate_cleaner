from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QLibraryInfo
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

from .bridge import AppBridge


SYSTEM_QML_IMPORT_PATHS = (
    "/usr/lib64/qt6/qml",
    "/usr/lib/qt6/qml",
    "/usr/local/lib64/qt6/qml",
    "/usr/local/lib/qt6/qml",
)
INSTALLED_QML_PATHS = (
    Path("/usr/share/duplicate-cleaner/qml/Main.qml"),
    Path("/usr/local/share/duplicate-cleaner/qml/Main.qml"),
)
INSTALLED_ICON_PATHS = (
    Path("/usr/share/icons/hicolor/scalable/apps/duplicate-cleaner.svg"),
    Path("/usr/local/share/icons/hicolor/scalable/apps/duplicate-cleaner.svg"),
)


def _resolve_app_icon() -> QIcon:
    themed_icon = QIcon.fromTheme("duplicate-cleaner")
    if not themed_icon.isNull():
        return themed_icon

    package_root = Path(__file__).resolve().parents[2]
    repo_icon = package_root / "packaging" / "assets" / "duplicate-cleaner.svg"
    if repo_icon.exists():
        return QIcon(str(repo_icon))

    for icon_path in INSTALLED_ICON_PATHS:
        if icon_path.exists():
            return QIcon(str(icon_path))

    return QIcon()


def _resolve_main_qml() -> Path:
    package_root = Path(__file__).resolve().parents[2]
    repo_qml = package_root / "qml" / "Main.qml"
    if repo_qml.exists():
        return repo_qml

    for installed_qml in INSTALLED_QML_PATHS:
        if installed_qml.exists():
            return installed_qml

    return repo_qml


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Duplicate Cleaner")
    app.setOrganizationName("isojanis")
    app.setDesktopFileName("duplicate-cleaner")
    app.setWindowIcon(_resolve_app_icon())

    qml_path = _resolve_main_qml()

    engine = QQmlApplicationEngine()

    qt_qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.QmlImportsPath)
    if qt_qml_path:
        engine.addImportPath(qt_qml_path)

    for import_path in SYSTEM_QML_IMPORT_PATHS:
        if Path(import_path).exists():
            engine.addImportPath(import_path)

    bridge = AppBridge(parent=engine)
    engine.rootContext().setContextProperty("appBridge", bridge)
    engine.load(str(qml_path))

    if not engine.rootObjects():
        return 1

    return app.exec()
