import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from PySide6.QtCore import QObject, QSettings, QtMsgType, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from duplicate_cleaner.app import _resolve_main_qml
from duplicate_cleaner.bridge import AppBridge


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
            bridge.setSelectedFolder(tmp)
            app.processEvents()
            scan_button = root.findChild(QObject, "scanButton")
            self.assertIsNotNone(scan_button)
            scan_button.clicked.emit()
            deadline = time.monotonic() + 10
            while bridge.get_is_scanning() and time.monotonic() < deadline:
                app.processEvents()
                time.sleep(0.005)
            self.assertFalse(bridge.get_is_scanning())
            self.assertEqual(bridge.get_scan_summary()["phase"], "Complete")
            self.assertEqual(bridge.get_scan_summary()["duplicateFiles"], 2)
            bridge.selectPreviewFile(str(Path(tmp) / "a.txt"))
            app.processEvents()
            # Context deprecations are Qt log messages, not engine.warnings.
            interaction_warnings = []
            def capture_message(kind, context, message):
                if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
                    interaction_warnings.append(message)
            previous_handler = qInstallMessageHandler(capture_message)
            try:
                for name, prop, values in (
                    ("sortFieldCombo", "sortField", ("size", "count")),
                    ("sortDirectionCombo", "sortDirection", ("descending", "ascending")),
                ):
                    combo = root.findChild(QObject, name)
                    self.assertIsNotNone(combo)
                    for index in (1, 0):
                        combo.activated.emit(index)
                        app.processEvents()
                        self.assertEqual(bridge.property(prop), values[index])
            finally:
                qInstallMessageHandler(previous_handler)
            self.assertEqual(interaction_warnings, [])
            self.assertEqual(warnings, [])
            root.close()
            bridge.shutdown()
            del root
            del engine
