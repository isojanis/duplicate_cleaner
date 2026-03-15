import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
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

    width: 1180
    height: 760
    visible: true
    title: "Duplicate Cleaner"

    pageStack.initialPage: Kirigami.ScrollablePage {
        title: "Duplicate Cleaner"

        ColumnLayout {
            width: parent.width
            spacing: Kirigami.Units.largeSpacing

            Kirigami.InlineMessage {
                Layout.fillWidth: true
                text: "Scan a folder, watch the current path in real time, and ignore unreadable files instead of failing the whole scan."
                type: Kirigami.MessageType.Information
                visible: true
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignTop
                spacing: Kirigami.Units.largeSpacing

                ColumnLayout {
                    Layout.preferredWidth: Math.min(360, parent.width * 0.34)
                    Layout.maximumWidth: 380
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignTop
                    spacing: Kirigami.Units.largeSpacing

                    Rectangle {
                        Layout.fillWidth: true
                        color: Kirigami.Theme.backgroundColor
                        radius: 12
                        border.color: Kirigami.Theme.disabledTextColor
                        border.width: 1
                        implicitHeight: content.implicitHeight + Kirigami.Units.largeSpacing * 2

                        ColumnLayout {
                            id: content
                            anchors.fill: parent
                            anchors.margins: Kirigami.Units.largeSpacing
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
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        color: Kirigami.Theme.backgroundColor
                        radius: 12
                        border.color: Kirigami.Theme.disabledTextColor
                        border.width: 1
                        implicitHeight: summaryColumn.implicitHeight + Kirigami.Units.largeSpacing * 2

                        ColumnLayout {
                            id: summaryColumn
                            anchors.fill: parent
                            anchors.margins: Kirigami.Units.largeSpacing
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

                            GridLayout {
                                Layout.fillWidth: true
                                columns: 2
                                columnSpacing: Kirigami.Units.largeSpacing
                                rowSpacing: Kirigami.Units.smallSpacing

                                Label { text: "Files scanned" }
                                Label { text: String(appBridge && appBridge.scanSummary ? appBridge.scanSummary.totalFiles : 0) }

                                Label { text: "Folders scanned" }
                                Label { text: String(appBridge && appBridge.scanSummary ? appBridge.scanSummary.totalFolders : 0) }

                                Label { text: "Skipped unreadable" }
                                Label { text: String(appBridge && appBridge.scanSummary ? appBridge.scanSummary.skippedFiles : 0) }

                                Label { text: "Live duplicate groups" }
                                Label { text: String(appBridge && appBridge.scanSummary ? appBridge.scanSummary.liveGroupCount : 0) }

                                Label { text: "Live duplicate files" }
                                Label { text: String(appBridge && appBridge.scanSummary ? appBridge.scanSummary.liveDuplicateFiles : 0) }

                                Label { text: "Hash progress" }
                                Label {
                                    text: appBridge && appBridge.scanSummary
                                        ? String(appBridge.scanSummary.hashedFiles) + " / " + String(appBridge.scanSummary.hashCandidates)
                                        : "0 / 0"
                                }

                                Label { text: "Final groups" }
                                Label { text: String(appBridge && appBridge.scanSummary ? appBridge.scanSummary.groupCount : 0) }

                                Label { text: "Final duplicate files" }
                                Label { text: String(appBridge && appBridge.scanSummary ? appBridge.scanSummary.duplicateFiles : 0) }

                                Label { text: "Wasted space" }
                                Label { text: root.formatBytes(appBridge && appBridge.scanSummary ? appBridge.scanSummary.wastedBytes : 0) }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.alignment: Qt.AlignTop
                    color: Kirigami.Theme.backgroundColor
                    radius: 12
                    border.color: Kirigami.Theme.disabledTextColor
                    border.width: 1
                    implicitHeight: duplicatesColumn.implicitHeight + Kirigami.Units.largeSpacing * 2

                    ColumnLayout {
                        id: duplicatesColumn
                        anchors.fill: parent
                        anchors.margins: Kirigami.Units.largeSpacing
                        spacing: Kirigami.Units.largeSpacing

                        RowLayout {
                            Layout.fillWidth: true

                            Label {
                                text: "Duplicate groups"
                                font.pointSize: 16
                                font.bold: true
                            }

                            Item {
                                Layout.fillWidth: true
                            }

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
                                ? "Scanning in progress. Live duplicate counts update as hashing confirms matches, and full groups appear when the scan completes."
                                : "No duplicate groups yet. Pick a folder and run a scan."
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: Kirigami.Units.largeSpacing

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

                                        Label {
                                            Layout.fillWidth: true
                                            color: Kirigami.Theme.disabledTextColor
                                            text: "Recoverable space: " + root.formatBytes(modelData.wastedBytes)
                                        }

                                        Repeater {
                                            model: modelData.files

                                            delegate: Label {
                                                required property string modelData

                                                Layout.fillWidth: true
                                                wrapMode: Text.WrapAnywhere
                                                text: modelData
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    FolderDialog {
        id: folderDialog
        currentFolder: appBridge ? "file://" + appBridge.selectedFolder : "file:///"
        onAccepted: appBridge.setSelectedFolder(selectedFolder.toString())
    }
}
