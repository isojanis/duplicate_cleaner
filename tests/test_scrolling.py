import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
import unittest

from PySide6.QtCore import QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication, QInputDevice, QPointingDevice, QWheelEvent
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
from duplicate_cleaner import scroll_input  # Register the production QML input type.


class ScrollingTests(unittest.TestCase):
    def setUp(self):
        self.app = QGuiApplication.instance() or QGuiApplication([])
        self.engine = QQmlApplicationEngine()
        self.warnings = []
        self.event_time = 0
        self.engine.warnings.connect(lambda messages: self.warnings.extend(m.toString() for m in messages))
        self.engine.loadData(b'''
            import QtQuick
            import "../qml/components"
            Window {
                width: 400; height: 240; visible: true
                SmoothFlickable {
                    objectName: "scroll"
                    anchors.fill: parent
                    contentHeight: 2000
                    Rectangle {
                        width: 380; height: 2000; color: "white"
                        MouseArea { anchors.fill: parent }
                    }
                }
            }
        ''', QUrl.fromLocalFile(str(Path(__file__).resolve())))
        self.assertTrue(self.engine.rootObjects(), self.warnings)
        self.window = self.engine.rootObjects()[0]
        self.view = self.window.findChild(QObject, "scroll")
        QTest.qWait(30)

    def tearDown(self):
        self.window.close()
        del self.view
        del self.window
        del self.engine
        self.app.processEvents()
        self.assertEqual(self.warnings, [])

    def wheel(self, angle=0, pixel=0, phase=Qt.ScrollPhase.NoScrollPhase, device=None):
        position = QPointF(120, 120)
        event = QWheelEvent(
            position, QPointF(self.window.mapToGlobal(position.toPoint())),
            QPoint(0, pixel), QPoint(0, angle), Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier, phase, False,
            Qt.MouseEventSource.MouseEventSynthesizedBySystem if device
            else Qt.MouseEventSource.MouseEventNotSynthesized,
            device or QPointingDevice.primaryPointingDevice(),
        )
        self.event_time += 20
        event.setTimestamp(self.event_time)
        self.app.sendEvent(self.window, event)

    def test_wheel_glides_and_accumulates_over_clickable_rows(self):
        self.wheel(angle=-120)
        self.assertTrue(self.view.property("wheelScrolling"))
        self.assertAlmostEqual(self.view.property("contentY"), 0, delta=1)
        QTest.qWait(70)
        midway = self.view.property("contentY")
        destination = self.view.property("wheelDestination")
        self.assertGreater(midway, 0)
        self.assertLess(midway, destination)
        self.wheel(angle=-120)
        self.assertGreater(self.view.property("wheelDestination"), destination)
        QTest.qWait(300)
        self.assertFalse(self.view.property("wheelScrolling"))
        self.assertAlmostEqual(self.view.property("contentY"), destination * 2, delta=1)

    def test_reversal_cancels_pending_travel_and_bounds_reset(self):
        self.view.setProperty("contentY", 200)
        self.wheel(angle=-360)
        QTest.qWait(50)
        position = self.view.property("contentY")
        self.wheel(angle=120)
        self.assertLess(self.view.property("wheelDestination"), position)
        QTest.qWait(300)
        self.assertLess(self.view.property("contentY"), position)
        self.wheel(angle=-120000)
        QTest.qWait(300)
        self.assertAlmostEqual(self.view.property("contentY"), 1760, delta=1)
        self.wheel(angle=120000)
        self.view.setProperty("contentHeight", 100)
        QTest.qWait(300)
        self.assertEqual(self.view.property("contentY"), 0)
        self.assertFalse(self.view.property("wheelScrolling"))

    def test_touchpad_pixels_and_momentum_use_native_scrolling(self):
        device = QPointingDevice(
            "test touchpad", 42, QInputDevice.DeviceType.TouchPad,
            QPointingDevice.PointerType.Finger,
            QInputDevice.Capability.Position | QInputDevice.Capability.Scroll | QInputDevice.Capability.PixelScroll,
            2, 0,
        )
        self.view.setProperty("contentY", 200)
        self.wheel(angle=-120)
        self.wheel(angle=-40, pixel=-20, phase=Qt.ScrollPhase.ScrollBegin, device=device)
        self.wheel(angle=-40, pixel=-20, phase=Qt.ScrollPhase.ScrollUpdate, device=device)
        self.assertFalse(self.view.property("wheelScrolling"))
        position = self.view.property("contentY")
        self.assertGreater(position, 200)
        self.wheel(angle=-20, pixel=-10, phase=Qt.ScrollPhase.ScrollMomentum, device=device)
        self.assertGreater(self.view.property("contentY"), position)
        self.wheel(phase=Qt.ScrollPhase.ScrollEnd, device=device)
        self.assertFalse(self.view.property("wheelScrolling"))

    def test_touchpad_glides_after_finger_lift_without_os_momentum(self):
        device = QPointingDevice(
            "test touchpad", 43, QInputDevice.DeviceType.TouchPad,
            QPointingDevice.PointerType.Finger,
            QInputDevice.Capability.Position | QInputDevice.Capability.Scroll | QInputDevice.Capability.PixelScroll,
            2, 0,
        )
        self.wheel(pixel=-32, phase=Qt.ScrollPhase.ScrollBegin, device=device)
        self.wheel(pixel=-32, phase=Qt.ScrollPhase.ScrollUpdate, device=device)
        before_lift = self.view.property("contentY")
        self.wheel(phase=Qt.ScrollPhase.ScrollEnd, device=device)
        self.assertTrue(self.view.property("flicking"))
        QTest.qWait(120)
        during_glide = self.view.property("contentY")
        self.assertGreater(during_glide, before_lift)
        QTest.qWait(250)
        self.assertGreater(self.view.property("contentY"), during_glide)

    def test_touchpad_without_scroll_phases_coasts_when_input_stops(self):
        device = QPointingDevice(
            "test phase-less touchpad", 44, QInputDevice.DeviceType.TouchPad,
            QPointingDevice.PointerType.Finger,
            QInputDevice.Capability.Position | QInputDevice.Capability.PixelScroll,
            2, 0,
        )
        self.wheel(pixel=-24, phase=Qt.ScrollPhase.NoScrollPhase, device=device)
        self.wheel(pixel=-24, phase=Qt.ScrollPhase.NoScrollPhase, device=device)
        before_lift = self.view.property("contentY")
        # Allow the quiet-period timer and first animation frame to run.
        QTest.qWait(220)
        self.assertGreater(self.view.property("contentY"), before_lift)
        self.assertTrue(self.view.property("flicking"))

    def test_scrollbar_interaction_stops_wheel_animation(self):
        self.wheel(angle=-360)
        QTest.qWait(30)
        bar = self.view.findChild(QQuickItem, "smoothVerticalScrollBar")
        self.assertIsNotNone(bar)
        position = bar.mapToScene(QPointF(bar.width() / 2, bar.height() / 2)).toPoint()
        QTest.mousePress(self.window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, position)
        try:
            self.assertTrue(bar.property("pressed"))
            self.assertFalse(self.view.property("wheelScrolling"))
        finally:
            QTest.mouseRelease(self.window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, position)
        position_after_drag = self.view.property("contentY")
        QTest.qWait(300)
        self.assertAlmostEqual(self.view.property("contentY"), position_after_drag, delta=1)
