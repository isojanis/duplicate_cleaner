import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Dialog {
    property var rootWindow

    title: "Run smart cleanup?"
    modal: true
    width: 480
    x: Math.round((rootWindow.width - width) / 2)
    y: Math.round((rootWindow.height - height) / 2)
    standardButtons: Dialog.Yes | Dialog.No

    onAccepted: if (appBridge) appBridge.applyMagicCleanup()

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.smallSpacing

        Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            font.bold: true
            text: "This will delete near-identical file-name hash duplicates that are in the same folder, keeping the oldest file in each match set."
        }

        Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: Kirigami.Theme.disabledTextColor
            text: appBridge && appBridge.magicCleanupCandidateCount > 0
                ? "You are about to delete " + appBridge.magicCleanupCandidateCount + " files. This cannot be undone from inside the app."
                : "No eligible files were found for smart cleanup."
        }
    }
}
