from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import QLibraryInfo, QSettings, QTimer
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from .bridge import AppBridge


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

    bundled_icon = Path(__file__).resolve().parent / "resources/assets/duplicate-cleaner.svg"
    if bundled_icon.exists():
        return QIcon(str(bundled_icon))
    package_root = Path(__file__).resolve().parents[2]
    repo_icon = package_root / "packaging" / "assets" / "duplicate-cleaner.svg"
    if repo_icon.exists():
        return QIcon(str(repo_icon))

    for icon_path in INSTALLED_ICON_PATHS:
        if icon_path.exists():
            return QIcon(str(icon_path))

    return QIcon()


def _resolve_main_qml() -> Path:
    bundled_qml = Path(__file__).resolve().parent / "resources/qml/Main.qml"
    if bundled_qml.exists():
        return bundled_qml
    package_root = Path(__file__).resolve().parents[2]
    repo_qml = package_root / "qml" / "Main.qml"
    if repo_qml.exists():
        return repo_qml

    for installed_qml in INSTALLED_QML_PATHS:
        if installed_qml.exists():
            return installed_qml

    return repo_qml


def main() -> int:
    smoke_test = "--smoke-test" in sys.argv
    test_settings = TemporaryDirectory(prefix="duplicate-cleaner-smoke-") if smoke_test else None
    if test_settings:
        QSettings.setDefaultFormat(QSettings.IniFormat)
        QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, test_settings.name)
    # Custom control backgrounds need a non-native style on Windows.
    if sys.platform == "win32":
        QQuickStyle.setStyle("Fusion")
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Duplicate Cleaner")
    app.setOrganizationName("isojanis")
    app.setDesktopFileName("duplicate-cleaner")
    app.setWindowIcon(_resolve_app_icon())

    qml_path = _resolve_main_qml()

    engine = QQmlApplicationEngine()
    warnings = []
    if smoke_test:
        engine.warnings.connect(lambda messages: warnings.extend(messages))

    qt_qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.QmlImportsPath)
    if qt_qml_path:
        engine.addImportPath(qt_qml_path)

    bridge = AppBridge(parent=engine)
    app.aboutToQuit.connect(bridge.shutdown)
    engine.rootContext().setContextProperty("appBridge", bridge)
    engine.load(str(qml_path))

    if not engine.rootObjects():
        return 1

    if smoke_test:
        QTimer.singleShot(500, lambda: app.exit(1 if warnings else 0))
    result = app.exec()
    if test_settings:
        test_settings.cleanup()
    return result
