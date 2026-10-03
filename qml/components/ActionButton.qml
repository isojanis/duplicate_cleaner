import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami

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
        color: control.highlighted && control.enabled ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
        opacity: control.enabled ? 1 : 0.4
    }
    background: Rectangle {
        radius: 8
        color: control.highlighted && control.enabled
            ? (control.down ? Qt.darker(Kirigami.Theme.highlightColor, 1.15) : Kirigami.Theme.highlightColor)
            : Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, control.hovered && control.enabled ? 0.08 : 0.035)
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? Kirigami.Theme.highlightColor : Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.1)
    }
}
