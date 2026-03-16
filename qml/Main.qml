import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import org.kde.kirigami as Kirigami
import "components"

Kirigami.ApplicationWindow {
    id: root

    function formatBytes(bytes) {
        if (bytes <= 0)
            return "0 B"

        const units = ["B", "KB", "MB", "GB", "TB"]
        let value = bytes
        let unitIndex = 0

        while (value >= 1024 && unitIndex < units.length - 1) {
            value /= 1024
            unitIndex += 1
        }

        const decimals = unitIndex === 0 ? 0 : 1
        return value.toFixed(decimals) + " " + units[unitIndex]
    }

    function formatSizeText(bytes) {
        if (bytes % (1024 * 1024 * 1024) === 0)
            return (bytes / (1024 * 1024 * 1024)) + " GB"
        if (bytes % (1024 * 1024) === 0)
            return (bytes / (1024 * 1024)) + " MB"
        if (bytes % 1024 === 0 && bytes !== 0)
            return (bytes / 1024) + " KB"
        return bytes + " B"
    }

    function compactResultPath(filePath) {
        if (!appBridge || !appBridge.selectedFolder)
            return filePath

        const scanFolder = appBridge.selectedFolder
        if (scanFolder === "/")
            return filePath

        const normalizedFolder = scanFolder.endsWith("/") ? scanFolder : scanFolder + "/"
        if (!filePath.startsWith(normalizedFolder))
            return filePath

        return ".../" + filePath.slice(normalizedFolder.length)
    }

    width: 1600
    height: 1100
    visible: true
    title: "Duplicate Cleaner"
    property bool scanSummaryExpanded: true
    property string appIconSource: "../packaging/assets/duplicate-cleaner.svg"

    pageStack.initialPage: Kirigami.Page {
        title: "Duplicate Cleaner"
        titleDelegate: RowLayout {
            spacing: Kirigami.Units.smallSpacing

            Image {
                Layout.preferredWidth: 24
                Layout.preferredHeight: 24
                source: root.appIconSource
                fillMode: Image.PreserveAspectFit
                smooth: true
            }

            Label {
                text: "Duplicate Cleaner"
                font.bold: true
            }
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing / 2
            spacing: Kirigami.Units.smallSpacing / 2

            ScanPanel {
                rootWindow: root
                folderDialog: folderDialog
                ignoreFoldersDialog: ignoreFoldersDialog
                ignoreExtensionsDialog: ignoreExtensionsDialog
            }

            SplitView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                orientation: Qt.Horizontal
                handle: Rectangle {
                    implicitWidth: 8
                    color: SplitHandle.hovered ? Kirigami.Theme.highlightColor : Kirigami.Theme.disabledTextColor
                    opacity: SplitHandle.pressed || SplitHandle.hovered ? 0.5 : 0.22
                    radius: 4
                }

                ResultsPane {
                    rootWindow: root
                    magicCleanupDialog: magicCleanupDialog
                }

                PreviewPane {
                    rootWindow: root
                }
            }
        }
    }

    MagicCleanupDialog {
        id: magicCleanupDialog
        rootWindow: root
    }

    IgnoreFoldersDialog {
        id: ignoreFoldersDialog
        rootWindow: root
    }

    IgnoreExtensionsDialog {
        id: ignoreExtensionsDialog
        rootWindow: root
    }

    FolderDialog {
        id: folderDialog
        currentFolder: appBridge ? "file://" + appBridge.selectedFolder : "file:///"
        onAccepted: appBridge.setSelectedFolder(selectedFolder.toString())
    }
}
