import QtQuick
import QtQuick.Controls
import DuplicateCleaner.Input 1.0

Flickable {
    id: view
    clip: true
    flickableDirection: Flickable.VerticalFlick
    boundsBehavior: Flickable.StopAtBounds
    maximumFlickVelocity: 2000
    flickDeceleration: 2600
    contentWidth: width

    readonly property real maximumY: Math.max(0, contentHeight - height)
    readonly property bool wheelScrolling: wheelAnimation.running
    property real wheelDestination: 0
    property bool touchpadGesture: false
    property bool systemMomentum: false
    property real touchpadVelocity: 0
    property real lastInputTime: 0

    function stopWheelScroll() {
        wheelAnimation.stop()
        wheelDestination = contentY
    }

    function resetTouchpad() {
        gestureTimeout.stop()
        touchpadGesture = false
        systemMomentum = false
        touchpadVelocity = 0
        lastInputTime = 0
    }

    function stopMomentum() {
        stopWheelScroll()
        resetTouchpad()
        cancelFlick()
    }

    function clampScroll() {
        if (!wheelAnimation) return
        stopMomentum()
        contentY = Math.max(0, Math.min(maximumY, contentY))
    }

    function scrollWheel(distance) {
        cancelFlick()
        // Accumulate a burst, but discard its remaining travel when reversing.
        const continuing = wheelAnimation.running
            && (wheelDestination - contentY) * distance > 0
        const destination = Math.max(0, Math.min(maximumY,
            (continuing ? wheelDestination : contentY) + distance))
        wheelAnimation.stop()
        wheelDestination = destination
        wheelAnimation.from = contentY
        wheelAnimation.to = destination
        if (Math.abs(destination - contentY) > 0.5)
            wheelAnimation.start()
    }

    function finishTouchpad() {
        gestureTimeout.stop()
        if (!systemMomentum && Math.abs(touchpadVelocity) > 80)
            flick(0, -touchpadVelocity)
        resetTouchpad()
    }

    function handleScroll(distance, phase, timestamp, precise) {
        if (!precise) {
            resetTouchpad()
            scrollWheel(distance)
            return
        }
        if (phase === Qt.ScrollBegin || !touchpadGesture) {
            stopMomentum()
            touchpadGesture = true
        }
        if (phase === Qt.ScrollMomentum) {
            // Native momentum takes over if the platform supplies it.
            systemMomentum = true
            cancelFlick()
        }
        if (phase === Qt.ScrollEnd) {
            if (timestamp - lastInputTime > 100)
                touchpadVelocity = 0
            finishTouchpad()
            return
        }
        stopWheelScroll()
        if (distance !== 0) {
            const elapsed = lastInputTime ? Math.max(1, timestamp - lastInputTime) : 16
            const sample = Math.max(-maximumFlickVelocity,
                Math.min(maximumFlickVelocity, distance * 1000 / elapsed))
            touchpadVelocity = elapsed > 100 || touchpadVelocity * sample <= 0
                ? sample : touchpadVelocity * 0.35 + sample * 0.65
            const previous = contentY
            contentY = Math.max(0, Math.min(maximumY, contentY + distance))
            if (contentY === previous) touchpadVelocity = 0
            lastInputTime = timestamp
        }
        // Some drivers send pixel deltas without scroll-phase markers.
        gestureTimeout.restart()
    }

    onContentHeightChanged: clampScroll()
    onHeightChanged: clampScroll()
    onDraggingChanged: if (dragging) { stopWheelScroll(); resetTouchpad() }

    NumberAnimation {
        id: wheelAnimation
        target: view
        property: "contentY"
        duration: 240
        easing.type: Easing.OutCubic
    }

    Timer {
        id: gestureTimeout
        interval: 100
        onTriggered: view.finishTouchpad()
    }

    // A viewport-sized sibling sees the original QWheelEvent phase and can
    // keep clicks on result rows and wheel input over the scrollbar working.
    ScrollWheelArea {
        parent: view.parent
        x: view.x
        y: view.y
        width: Math.max(0, view.width - verticalBar.width)
        height: view.height
        z: view.z + 1
        onScrolled: function(distance, phase, timestamp, precise) {
            view.handleScroll(distance, phase, timestamp, precise)
        }
    }

    ScrollBar.vertical: ScrollBar {
        id: verticalBar
        objectName: "smoothVerticalScrollBar"
        active: view.wheelScrolling || view.touchpadGesture || view.moving || hovered || pressed
        onPressedChanged: if (pressed) view.stopMomentum()
    }
}
