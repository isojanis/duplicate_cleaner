import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from PySide6.QtCore import QSettings
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from duplicate_cleaner.app import _resolve_main_qml
from duplicate_cleaner.bridge import AppBridge
from duplicate_cleaner.scanner import scan_for_duplicates


class QmlTests(unittest.TestCase):
    def test_full_interface_loads(self):
        app = QGuiApplication.instance() or QGuiApplication([])
        QQuickStyle.setStyle("Fusion")
        with TemporaryDirectory() as tmp:
            engine = QQmlApplicationEngine()
            settings = QSettings(str(Path(tmp) / "settings.ini"), QSettings.IniFormat)
            with patch("duplicate_cleaner.bridge.QSettings", return_value=settings):
                bridge = AppBridge(parent=engine)
            warnings = []
            engine.warnings.connect(lambda messages: warnings.extend(m.toString() for m in messages))
            engine.rootContext().setContextProperty("appBridge", bridge)
            engine.load(str(_resolve_main_qml()))
            self.assertTrue(engine.rootObjects(), warnings)
            root = engine.rootObjects()[0]
            root.setProperty("width", 960)
            root.setProperty("height", 680)
            root.setProperty("scanSummaryExpanded", True)
            for name in ("a.txt", "b.txt"):
                (Path(tmp) / name).write_text("Preview content")
            bridge._complete_scan(scan_for_duplicates(Path(tmp)))
            bridge.selectPreviewFile(str(Path(tmp) / "a.txt"))
            app.processEvents()
            self.assertEqual(warnings, [])
            root.close()
            bridge.shutdown()
            del root
            del engine
