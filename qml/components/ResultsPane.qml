import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Frame {
    property var rootWindow
    property var magicCleanupDialog

    SplitView.fillWidth: true
    SplitView.preferredWidth: 700
    SplitView.minimumWidth: 380
    padding: 0
    background: Rectangle {
        color: Kirigami.Theme.backgroundColor
        radius: 8
        border.color: Kirigami.Theme.disabledTextColor
        border.width: 1
    }

    ScrollView {
        id: resultsPaneScroll
        anchors.fill: parent
        anchors.margins: 1
        clip: true

        ColumnLayout {
            x: Kirigami.Units.smallSpacing
            y: Kirigami.Units.smallSpacing
            width: Math.max(0, resultsPaneScroll.availableWidth - Kirigami.Units.smallSpacing * 2)
            spacing: Kirigami.Units.smallSpacing

            RowLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing

                Label {
                    text: "Duplicate groups"
                    font.pointSize: 16
                    font.bold: true
                }

                Button {
                    text: appBridge && appBridge.magicCleanupCandidateCount > 0
                        ? "Smart cleanup (" + appBridge.magicCleanupCandidateCount + ")"
                        : "Smart cleanup"
                    enabled: appBridge ? appBridge.magicCleanupCandidateCount > 0 : false
                    onClicked: magicCleanupDialog.open()
                }

                Item { Layout.fillWidth: true }

                Label {
                    text: "Sort by"
                    color: Kirigami.Theme.disabledTextColor
                }

                ComboBox {
                    Layout.preferredWidth: 150
                    model: [
                        { text: "Size of files", value: "size" },
                        { text: "Number of matches", value: "count" }
                    ]
                    textRole: "text"
                    Component.onCompleted: currentIndex = appBridge && appBridge.sortField === "count" ? 1 : 0
                    onActivated: if (appBridge) appBridge.setSortField(model[index].value)
                }

                ComboBox {
                    Layout.preferredWidth: 130
                    model: [
                        { text: "Descending", value: "descending" },
                        { text: "Ascending", value: "ascending" }
                    ]
                    textRole: "text"
                    Component.onCompleted: currentIndex = appBridge && appBridge.sortDirection === "ascending" ? 1 : 0
                    onActivated: if (appBridge) appBridge.setSortDirection(model[index].value)
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
                    ? "Scanning in progress. Full groups appear when the scan completes, and you can preview files by clicking them afterward."
                    : "No duplicate groups yet. Pick a folder and run a scan."
            }

            Repeater {
                model: appBridge ? appBridge.duplicateGroups : []

                delegate: Rectangle {
                    required property var modelData

                    Layout.fillWidth: true
                    color: Kirigami.Theme.alternateBackgroundColor
                    radius: 8
                    border.color: Kirigami.Theme.disabledTextColor
                    border.width: 1
                    implicitHeight: duplicateCard.implicitHeight + Kirigami.Units.largeSpacing * 2

                    ColumnLayout {
                        id: duplicateCard
                        anchors.fill: parent
                        anchors.margins: Kirigami.Units.smallSpacing
                        spacing: Kirigami.Units.smallSpacing

                        RowLayout {
                            Layout.fillWidth: true

                            Label {
                                Layout.fillWidth: true
                                font.bold: true
                                text: modelData.count + " matching files"
                            }

                            Label {
                                text: rootWindow.formatBytes(modelData.sizeBytes) + " each"
                                color: Kirigami.Theme.disabledTextColor
                            }
                        }

                        Repeater {
                            model: modelData.files

                            delegate: Rectangle {
                                required property string modelData
                                property bool deleted: appBridge ? appBridge.deletedPaths.indexOf(modelData) !== -1 : false

                                Layout.fillWidth: true
                                color: appBridge && appBridge.previewData && appBridge.previewData.path === modelData
                                    ? Kirigami.Theme.highlightColor
                                    : "transparent"
                                radius: 4
                                implicitHeight: fileLabel.implicitHeight + Kirigami.Units.smallSpacing * 2

                                Label {
                                    id: fileLabel
                                    anchors.fill: parent
                                    anchors.margins: Kirigami.Units.smallSpacing
                                    wrapMode: Text.WrapAnywhere
                                    font.italic: parent.deleted
                                    font.strikeout: parent.deleted
                                    color: parent.deleted
                                        ? "#b24a4a"
                                        : (parent.color === "transparent"
                                            ? Kirigami.Theme.linkColor
                                            : Kirigami.Theme.highlightedTextColor)
                                    text: rootWindow.compactResultPath(modelData)
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                                    cursorShape: parent.deleted ? Qt.ArrowCursor : Qt.PointingHandCursor
                                    onClicked: function(mouse) {
                                        if (mouse.button === Qt.LeftButton)
                                            appBridge.selectPreviewFile(modelData)
                                        if (mouse.button === Qt.RightButton && !parent.deleted)
                                            fileMenu.popup()
                                    }
                                }

                                Menu {
                                    id: fileMenu

                                    MenuItem {
                                        text: "Delete"
                                        onTriggered: deleteDialog.open()
                                    }

                                    MenuSeparator {}

                                    MenuItem {
                                        text: "Show in folder"
                                        onTriggered: appBridge.showInFolder(modelData)
                                    }
                                }

                                Dialog {
                                    id: deleteDialog
                                    title: "Delete file?"
                                    modal: true
                                    standardButtons: Dialog.Yes | Dialog.No
                                    onAccepted: appBridge.deleteFile(modelData)

                                    contentItem: Label {
                                        width: 320
                                        wrapMode: Text.WordWrap
                                        text: "Are you sure you want to delete this file?\n\n" + modelData
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
