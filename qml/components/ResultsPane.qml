import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Frame {
    id: resultsPane
    property var rootWindow
    property var magicCleanupDialog

    SplitView.fillWidth: true
    SplitView.preferredWidth: 780
    SplitView.minimumWidth: 500
    padding: 0
    background: Rectangle {
        color: rootWindow.palette.base
        radius: 12
        border.color: rootWindow.subtleBorder
        border.width: 1
    }

    ScrollView {
        id: resultsPaneScroll
        anchors.fill: parent
        anchors.margins: 1
        clip: true

        ColumnLayout {
            x: 20
            y: 20
            width: Math.max(0, resultsPaneScroll.availableWidth - 40)
            spacing: Kirigami.Units.smallSpacing

            RowLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing

                Label {
                    text: "Duplicates"
                    font.pixelSize: 18
                    font.bold: true
                }

                ActionButton {
                    text: appBridge && appBridge.magicCleanupCandidateCount > 0
                        ? "Smart cleanup (" + appBridge.magicCleanupCandidateCount + ")"
                        : "Smart cleanup"
                    enabled: appBridge ? appBridge.magicCleanupCandidateCount > 0 : false
                    onClicked: magicCleanupDialog.open()
                }

                Item { Layout.fillWidth: true }


                Label {
                    text: appBridge && appBridge.scanSummary
                        ? String(appBridge.scanSummary.groupCount) + " groups"
                        : "0 groups"
                    color: rootWindow.mutedText
                }
            }

            RowLayout {
                Layout.fillWidth: true
                visible: appBridge && appBridge.duplicateGroups.length > 0
                spacing: 8
                Label {
                    text: "Sort by"
                    color: rootWindow.mutedText
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

                Item { Layout.fillWidth: true }
            }
            Item {
                Layout.fillWidth: true
                visible: !appBridge || appBridge.duplicateGroups.length === 0
                implicitHeight: Math.max(150, resultsPane.height - 100)
                ColumnLayout {
                    anchors.centerIn: parent
                    width: Math.min(parent.width - 40, 360)
                    spacing: 14
                    Kirigami.Icon {
                        source: appBridge && appBridge.isScanning ? "edit-find" : "folder-open"
                        Layout.alignment: Qt.AlignHCenter
                        Layout.preferredWidth: 52
                        Layout.preferredHeight: 52
                        opacity: 0.5
                        visible: resultsPane.height > 300
                    }
                    Label {
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignHCenter
                        font.pixelSize: 19
                        font.weight: Font.DemiBold
                        text: appBridge && appBridge.isScanning ? "Looking for duplicates…" : (appBridge && appBridge.scanSummary.totalFiles > 0 ? "No duplicates found" : "A little space, reclaimed")
                    }
                    Label {
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                        color: rootWindow.mutedText
                        text: appBridge && appBridge.isScanning ? "Comparing file contents. Results appear when the scan finishes." : (appBridge && appBridge.scanSummary.totalFiles > 0 ? "No matching files were found with the current filters." : "Choose a folder and start a scan. Review matching files here before deciding what to remove.")
                    }
                }
            }

            Repeater {
                model: appBridge ? appBridge.duplicateGroups : []

                delegate: Rectangle {
                    required property var modelData

                    Layout.fillWidth: true
                    color: rootWindow.mutedSurface
                    radius: 12
                    border.color: rootWindow.subtleBorder
                    border.width: 1
                    implicitHeight: duplicateCard.implicitHeight + 32

                    ColumnLayout {
                        id: duplicateCard
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 10

                        RowLayout {
                            Layout.fillWidth: true

                            Label {
                                Layout.fillWidth: true
                                font.bold: true
                                text: modelData.count + " matching files"
                            }

                            Label {
                                text: rootWindow.formatBytes(modelData.sizeBytes) + " each"
                                color: rootWindow.mutedText
                            }
                        }

                        Repeater {
                            model: modelData.files

                            delegate: Rectangle {
                                required property string modelData
                                property bool selected: appBridge && appBridge.previewData && appBridge.previewData.path === modelData
                                property bool deleted: appBridge ? appBridge.deletedPaths.indexOf(modelData) !== -1 : false

                                Layout.fillWidth: true
                                color: selected ? Qt.rgba(Kirigami.Theme.highlightColor.r, Kirigami.Theme.highlightColor.g, Kirigami.Theme.highlightColor.b, 0.12) : (fileMouse.containsMouse ? rootWindow.mutedSurface : "transparent")
                                radius: 4
                                implicitHeight: Math.max(42, fileLabel.implicitHeight + 20)

                                Label {
                                    id: fileLabel
                                    anchors.fill: parent
                                    anchors.margins: Kirigami.Units.smallSpacing
                                    wrapMode: Text.WrapAnywhere
                                    font.italic: parent.deleted
                                    font.strikeout: parent.deleted
                                    color: parent.deleted
                                        ? "#b24a4a"
                                        : (parent.selected ? Kirigami.Theme.linkColor : Kirigami.Theme.textColor)
                                    text: rootWindow.compactResultPath(modelData)
                                }

                                MouseArea {
                                    id: fileMouse
                                    hoverEnabled: true
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
