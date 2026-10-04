import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
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
        filePath = filePath.replace(/\\/g, "/")
        if (!appBridge || !appBridge.selectedFolder)
            return filePath

        const scanFolder = appBridge.selectedFolder.replace(/\\/g, "/")
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
    color: root.palette.window
    property bool scanSummaryExpanded: false
    property bool closeWhenStopped: false
    onClosing: function(event) {
        if (appBridge.isScanning || appBridge.isCleaning) {
            event.accepted = false
            closeWhenStopped = true
            appBridge.stopScan()
            appBridge.stopCleanup()
        }
    }
    Connections {
        target: appBridge
        function onIsScanningChanged() {
            if (root.closeWhenStopped && !appBridge.isScanning && !appBridge.isCleaning)
                root.close()
        }
        function onIsCleaningChanged() {
            if (root.closeWhenStopped && !appBridge.isScanning && !appBridge.isCleaning)
                root.close()
        }
    }
    Shortcut { sequence: "Ctrl+O"; enabled: !appBridge.isScanning && !appBridge.isCleaning; onActivated: folderDialog.open() }
    Shortcut { sequence: "Escape"; enabled: appBridge.isScanning || appBridge.isCleaning; onActivated: { appBridge.stopScan(); appBridge.stopCleanup() } }
    readonly property color mutedText: Qt.rgba(root.palette.text.r, root.palette.text.g, root.palette.text.b, 0.62)
    readonly property color subtleBorder: Qt.rgba(root.palette.text.r, root.palette.text.g, root.palette.text.b, 0.10)
    readonly property color mutedSurface: Qt.rgba(root.palette.text.r, root.palette.text.g, root.palette.text.b, 0.035)

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 20

        ScrollView {
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(scanPanel.implicitHeight, root.height * 0.55)
            clip: true
            contentWidth: availableWidth
            ScanPanel {
                id: scanPanel
                width: parent.width
                rootWindow: root
                folderDialog: folderDialog
                ignoreFoldersDialog: ignoreFoldersDialog
                ignoreExtensionsDialog: ignoreExtensionsDialog
            }
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
                    color: SplitHandle.hovered ? root.palette.highlight : root.subtleBorder
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
        currentFolder: appBridge ? appBridge.fileUrl(appBridge.selectedFolder) : "file:///"
        onAccepted: appBridge.setSelectedFolder(selectedFolder.toString())
    }
}
