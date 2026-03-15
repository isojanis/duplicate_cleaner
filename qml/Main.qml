import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import QtQuick.Pdf
import org.kde.kirigami as Kirigami

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

    width: 1480
    height: 800
    visible: true
    title: "Duplicate Cleaner"

    pageStack.initialPage: Kirigami.Page {
        title: "Duplicate Cleaner"

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.largeSpacing

            Frame {
                Layout.fillWidth: true
                Layout.minimumHeight: 200
                padding: 0
                background: Rectangle {
                    color: Kirigami.Theme.backgroundColor
                    radius: 12
                    border.color: Kirigami.Theme.disabledTextColor
                    border.width: 1
                }

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Kirigami.Units.largeSpacing
                    spacing: Kirigami.Units.largeSpacing

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Kirigami.Units.largeSpacing

                        Label {
                            text: "Scan folder"
                            font.pointSize: 16
                            font.bold: true
                        }

                        ComboBox {
                            id: folderField
                            Layout.fillWidth: true
                            editable: true
                            enabled: appBridge ? !appBridge.isScanning : false
                            model: appBridge ? appBridge.recentFolders : []

                            Component.onCompleted: {
                                if (appBridge)
                                    editText = appBridge.selectedFolder
                            }

                            onAccepted: appBridge.setSelectedFolder(editText)
                            onActivated: appBridge.setSelectedFolder(currentText)
                            onActiveFocusChanged: {
                                if (!activeFocus && appBridge)
                                    appBridge.setSelectedFolder(editText)
                            }
                        }

                        Button {
                            text: "Choose folder"
                            enabled: appBridge ? !appBridge.isScanning : false
                            onClicked: folderDialog.open()
                        }

                        Button {
                            text: appBridge && appBridge.isScanning ? "Stop scan" : "Start scan"
                            highlighted: true
                            onClicked: appBridge.startScan()
                        }
                    }

                    Connections {
                        target: appBridge

                        function onSelectedFolderChanged() {
                            if (!folderField.activeFocus)
                                folderField.editText = appBridge.selectedFolder
                        }

                        function onRecentFoldersChanged() {
                            if (!folderField.activeFocus)
                                folderField.editText = appBridge.selectedFolder
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Kirigami.Units.largeSpacing

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: Kirigami.Units.smallSpacing

                            Label {
                                text: appBridge && appBridge.isScanning ? "Live scan status" : "Scan summary"
                                font.pointSize: 16
                                font.bold: true
                            }

                            Label {
                                Layout.fillWidth: true
                                wrapMode: Text.WordWrap
                                text: appBridge ? appBridge.statusText : "Loading..."
                            }

                            Label {
                                Layout.fillWidth: true
                                visible: appBridge ? appBridge.isScanning : false
                                wrapMode: Text.WrapAnywhere
                                text: "Current path: " + (appBridge && appBridge.scanSummary ? appBridge.scanSummary.currentPath : "")
                                color: Kirigami.Theme.disabledTextColor
                            }
                        }

                        Flow {
                            Layout.fillWidth: true
                            Layout.alignment: Qt.AlignTop
                            spacing: Kirigami.Units.largeSpacing

                            Repeater {
                                model: [
                                    { label: "Files scanned", value: String(appBridge && appBridge.scanSummary ? appBridge.scanSummary.totalFiles : 0) },
                                    { label: "Folders scanned", value: String(appBridge && appBridge.scanSummary ? appBridge.scanSummary.totalFolders : 0) },
                                    { label: "Skipped unreadable", value: String(appBridge && appBridge.scanSummary ? appBridge.scanSummary.skippedFiles : 0) },
                                    { label: "Duplicate groups", value: String(appBridge && appBridge.scanSummary ? appBridge.scanSummary.groupCount : 0) },
                                    { label: "Duplicate files", value: String(appBridge && appBridge.scanSummary ? appBridge.scanSummary.duplicateFiles : 0) },
                                    { label: "Hash progress", value: appBridge && appBridge.scanSummary ? String(appBridge.scanSummary.hashedFiles) + " / " + String(appBridge.scanSummary.hashCandidates) : "0 / 0" },
                                                                                                            { label: "Wasted space", value: root.formatBytes(appBridge && appBridge.scanSummary ? appBridge.scanSummary.wastedBytes : 0) }
                                ]

                                delegate: Rectangle {
                                    required property var modelData

                                    implicitWidth: Math.max(132, statsColumn.implicitWidth + Kirigami.Units.smallSpacing * 2)
                                    height: statsColumn.implicitHeight + Kirigami.Units.smallSpacing * 2
                                    radius: 8
                                    color: Kirigami.Theme.alternateBackgroundColor
                                    border.color: Kirigami.Theme.disabledTextColor
                                    border.width: 1

                                    Column {
                                        id: statsColumn
                                        anchors.fill: parent
                                        anchors.margins: Kirigami.Units.smallSpacing
                                        spacing: 2

                                        Label {
                                            wrapMode: Text.WordWrap
                                            text: modelData.label
                                            color: Kirigami.Theme.disabledTextColor
                                        }

                                        Label {
                                            wrapMode: Text.WordWrap
                                            font.bold: true
                                            text: modelData.value
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
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

                Frame {
                    SplitView.fillWidth: true
                    SplitView.preferredWidth: 700
                    SplitView.minimumWidth: 380
                    padding: 0
                    background: Rectangle {
                        color: Kirigami.Theme.backgroundColor
                        radius: 12
                        border.color: Kirigami.Theme.disabledTextColor
                        border.width: 1
                    }

                    ScrollView {
                        id: resultsPaneScroll
                        anchors.fill: parent
                        anchors.margins: 1
                        clip: true

                        ColumnLayout {
                            x: Kirigami.Units.largeSpacing
                            y: Kirigami.Units.largeSpacing
                            width: Math.max(0, resultsPaneScroll.availableWidth - Kirigami.Units.largeSpacing * 2)
                            spacing: Kirigami.Units.largeSpacing

                            RowLayout {
                                Layout.fillWidth: true

                                Label {
                                    text: "Duplicate groups"
                                    font.pointSize: 16
                                    font.bold: true
                                }

                                Item { Layout.fillWidth: true }

                                Label {
                                    text: appBridge && appBridge.scanSummary
                                        ? String(appBridge.scanSummary.groupCount) + " groups"
                                        : "0 groups"
                                    color: Kirigami.Theme.disabledTextColor
                                }
                            }

                            Label {
                                Layout.fillWidth: true
                                visible: !appBridge || appBridge.duplicateGroups.length === 0
                                wrapMode: Text.WordWrap
                                color: Kirigami.Theme.disabledTextColor
                                text: appBridge && appBridge.isScanning
                                    ? "Scanning in progress. Full groups appear when the scan completes, and you can preview files by clicking them afterward."
                                    : "No duplicate groups yet. Pick a folder and run a scan."
                            }

                            Repeater {
                                model: appBridge ? appBridge.duplicateGroups : []

                                delegate: Rectangle {
                                    required property var modelData

                                    Layout.fillWidth: true
                                    color: Kirigami.Theme.alternateBackgroundColor
                                    radius: 10
                                    border.color: Kirigami.Theme.disabledTextColor
                                    border.width: 1
                                    implicitHeight: duplicateCard.implicitHeight + Kirigami.Units.largeSpacing * 2

                                    ColumnLayout {
                                        id: duplicateCard
                                        anchors.fill: parent
                                        anchors.margins: Kirigami.Units.largeSpacing
                                        spacing: Kirigami.Units.smallSpacing

                                        RowLayout {
                                            Layout.fillWidth: true

                                            Label {
                                                Layout.fillWidth: true
                                                font.bold: true
                                                text: modelData.count + " matching files"
                                            }

                                            Label {
                                                text: root.formatBytes(modelData.sizeBytes) + " each"
                                                color: Kirigami.Theme.disabledTextColor
                                            }
                                        }

                                        Repeater {
                                            model: modelData.files

                                            delegate: Rectangle {
                                                required property string modelData

                                                Layout.fillWidth: true
                                                color: appBridge && appBridge.previewData && appBridge.previewData.path === modelData
                                                    ? Kirigami.Theme.highlightColor
                                                    : "transparent"
                                                radius: 6
                                                implicitHeight: fileLabel.implicitHeight + Kirigami.Units.smallSpacing * 2

                                                Label {
                                                    id: fileLabel
                                                    anchors.fill: parent
                                                    anchors.margins: Kirigami.Units.smallSpacing
                                                    wrapMode: Text.WrapAnywhere
                                                    color: parent.color === "transparent"
                                                        ? Kirigami.Theme.linkColor
                                                        : Kirigami.Theme.highlightedTextColor
                                                    text: root.compactResultPath(modelData)
                                                }

                                                MouseArea {
                                                    anchors.fill: parent
                                                    cursorShape: Qt.PointingHandCursor
                                                    onClicked: appBridge.selectPreviewFile(modelData)
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                Frame {
                    SplitView.preferredWidth: 560
                    SplitView.minimumWidth: 400
                    SplitView.maximumWidth: 840
                    padding: 0
                    background: Rectangle {
                        color: Kirigami.Theme.backgroundColor
                        radius: 12
                        border.color: Kirigami.Theme.disabledTextColor
                        border.width: 1
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: Kirigami.Units.largeSpacing
                        spacing: Kirigami.Units.largeSpacing

                        RowLayout {
                            Layout.fillWidth: true

                            Label {
                                text: "File preview"
                                font.pointSize: 16
                                font.bold: true
                            }

                            Item { Layout.fillWidth: true }

                            Button {
                                text: "Open Folder"
                                enabled: appBridge && appBridge.previewData && appBridge.previewData.path !== ""
                                onClicked: appBridge.openPreviewFolder()
                            }
                        }

                        Label {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            font.bold: true
                            text: appBridge && appBridge.previewData ? appBridge.previewData.name : "No file selected"
                        }

                        Label {
                            Layout.fillWidth: true
                            wrapMode: Text.WrapAnywhere
                            color: Kirigami.Theme.disabledTextColor
                            text: appBridge && appBridge.previewData ? appBridge.previewData.path : ""
                        }

                        GridLayout {
                            Layout.fillWidth: true
                            columns: 2
                            columnSpacing: Kirigami.Units.largeSpacing
                            rowSpacing: Kirigami.Units.smallSpacing

                            Label { text: "Type" }
                            Label { text: appBridge && appBridge.previewData ? (appBridge.previewData.suffix || "unknown") : "" }
                            Label { text: "Size" }
                            Label { text: root.formatBytes(appBridge && appBridge.previewData ? appBridge.previewData.sizeBytes : 0) }
                            Label { text: "Hash" }
                            Label {
                                Layout.fillWidth: true
                                wrapMode: Text.WrapAnywhere
                                text: appBridge && appBridge.previewData ? appBridge.previewData.fileHash : ""
                            }
                        }

                        Label {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            color: Kirigami.Theme.disabledTextColor
                            text: appBridge && appBridge.previewData ? appBridge.previewData.statusText : ""
                        }

                        Label {
                            Layout.fillWidth: true
                            visible: appBridge && appBridge.previewData ? appBridge.previewData.isTruncated : false
                            wrapMode: Text.WordWrap
                            color: Kirigami.Theme.disabledTextColor
                            text: "Preview truncated for large text files."
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: Kirigami.Theme.alternateBackgroundColor
                            radius: 10
                            border.color: Kirigami.Theme.disabledTextColor
                            border.width: 1
                            clip: true

                            Loader {
                                anchors.fill: parent
                                anchors.margins: Kirigami.Units.smallSpacing
                                active: appBridge && appBridge.previewData
                                sourceComponent: {
                                    if (!appBridge || !appBridge.previewData)
                                        return emptyPreview
                                    if (appBridge.previewData.previewKind === "image")
                                        return imagePreview
                                    if (appBridge.previewData.previewKind === "text")
                                        return textPreview
                                    if (appBridge.previewData.previewKind === "pdf")
                                        return pdfPreview
                                    return emptyPreview
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Component {
        id: imagePreview

        Item {
            Image {
                anchors.fill: parent
                fillMode: Image.PreserveAspectFit
                source: appBridge.previewData.previewUrl
            }
        }
    }

    Component {
        id: textPreview

        ScrollView {
            TextArea {
                readOnly: true
                wrapMode: TextEdit.WrapAnywhere
                text: appBridge.previewData.textContent
            }
        }
    }

    Component {
        id: pdfPreview

        Item {
            PdfDocument {
                id: pdfDocument
                source: appBridge.previewData.previewUrl
            }

            PdfMultiPageView {
                anchors.fill: parent
                document: pdfDocument
            }
        }
    }

    Component {
        id: emptyPreview

        Item {
            Label {
                anchors.centerIn: parent
                width: Math.min(parent.width - 24, 260)
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                color: Kirigami.Theme.disabledTextColor
                text: appBridge && appBridge.previewData ? appBridge.previewData.textContent : "Select a file to preview it here."
            }
        }
    }

    FolderDialog {
        id: folderDialog
        currentFolder: appBridge ? "file://" + appBridge.selectedFolder : "file:///"
        onAccepted: appBridge.setSelectedFolder(selectedFolder.toString())
    }
}
