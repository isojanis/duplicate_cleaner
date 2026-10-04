import QtQuick
import QtQuick.Controls

Button {
    id: control
    implicitHeight: 40
    implicitWidth: label.implicitWidth + 32
    padding: 12
    hoverEnabled: true
    contentItem: Label {
        id: label
        text: control.text
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        font.weight: Font.DemiBold
        color: control.highlighted && control.enabled ? control.palette.highlightedText : control.palette.text
        opacity: control.enabled ? 1 : 0.4
    }
    background: Rectangle {
        radius: 8
        color: control.highlighted && control.enabled
            ? (control.down ? Qt.darker(control.palette.highlight, 1.15) : control.palette.highlight)
            : Qt.rgba(control.palette.text.r, control.palette.text.g, control.palette.text.b, control.hovered && control.enabled ? 0.08 : 0.035)
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? control.palette.highlight : Qt.rgba(control.palette.text.r, control.palette.text.g, control.palette.text.b, 0.1)
    }
}
