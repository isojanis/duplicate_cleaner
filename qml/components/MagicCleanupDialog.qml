import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

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
        spacing: 6

        Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            font.bold: true
            text: "Move identical-content files with similar names in the same folder to Trash / Recycle Bin, keeping the file with the oldest modification time. Changed files and last copies are skipped."
        }

        Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: rootWindow.palette.placeholderText
            text: appBridge && appBridge.magicCleanupCandidateCount > 0
                ? "Up to " + appBridge.magicCleanupCandidateCount + " files will be moved. Restore them through your system's Trash / Recycle Bin."
                : "No eligible files were found for smart cleanup."
        }
    }
}
