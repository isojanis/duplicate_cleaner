import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import org.kde.kirigami as Kirigami
import "components"

ApplicationWindow {
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

    width: 1280
    height: 860
    minimumWidth: 960
    minimumHeight: 680
    visible: true
    title: "Duplicate Cleaner"
    color: Kirigami.Theme.backgroundColor
    property bool scanSummaryExpanded: false
    readonly property color mutedText: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.62)
    readonly property color subtleBorder: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.10)
    readonly property color mutedSurface: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.035)

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 20

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
            handle: Item {
                implicitWidth: 16
                Rectangle {
                    anchors.centerIn: parent
                    width: 3
                    height: 32
                    radius: 2
                    color: SplitHandle.hovered ? Kirigami.Theme.highlightColor : root.subtleBorder
                }
            }
            ResultsPane { rootWindow: root; magicCleanupDialog: magicCleanupDialog }
            PreviewPane { rootWindow: root }
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
