import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Frame {
    id: resultsPane
    property var rootWindow
    property var magicCleanupDialog
    readonly property string scanPhase: appBridge ? appBridge.scanSummary.phase : "Idle"

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

    SmoothFlickable {
        id: resultsPaneScroll
        objectName: "duplicateResultsScroll"
        anchors.fill: parent
        anchors.margins: 1
        contentHeight: resultsColumn.implicitHeight + 40

        ColumnLayout {
            id: resultsColumn
            x: 20
            y: 20
            width: Math.max(0, resultsPaneScroll.width - 40)
            spacing: 6

            RowLayout {
                Layout.fillWidth: true
                spacing: 6

                Label {
                    text: "Duplicates"
                    font.pixelSize: 18
                    font.bold: true
                }

                ActionButton {
                    text: appBridge && appBridge.magicCleanupCandidateCount > 0
                        ? "Smart cleanup (" + appBridge.magicCleanupCandidateCount + ")"
                        : "Smart cleanup"
                    enabled: appBridge ? appBridge.magicCleanupCandidateCount > 0 && !appBridge.isCleaning : false
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
                    objectName: "sortFieldCombo"
                    Layout.preferredWidth: 150
                    model: [
                        { text: "Size of files", value: "size" },
                        { text: "Number of matches", value: "count" }
                    ]
                    textRole: "text"
                    Component.onCompleted: currentIndex = appBridge && appBridge.sortField === "count" ? 1 : 0
                    onActivated: function(index) {
                        if (appBridge) appBridge.setSortField(model[index].value)
                    }
                }

                ComboBox {
                    objectName: "sortDirectionCombo"
                    Layout.preferredWidth: 130
                    model: [
                        { text: "Descending", value: "descending" },
                        { text: "Ascending", value: "ascending" }
                    ]
                    textRole: "text"
                    Component.onCompleted: currentIndex = appBridge && appBridge.sortDirection === "ascending" ? 1 : 0
                    onActivated: function(index) {
                        if (appBridge) appBridge.setSortDirection(model[index].value)
                    }
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
                    Label {
                        text: "≡"
                        font.pixelSize: 44
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
                        text: appBridge && appBridge.isScanning ? "Looking for duplicates…"
                            : resultsPane.scanPhase === "Limited" ? "Search limit reached"
                            : resultsPane.scanPhase === "Stopped" ? "Scan stopped"
                            : resultsPane.scanPhase === "Failed" ? "Scan failed"
                            : resultsPane.scanPhase === "Complete" ? "No duplicates found"
                            : "A little space, reclaimed"
                    }
                    Label {
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                        color: rootWindow.mutedText
                        text: appBridge && appBridge.isScanning ? appBridge.statusText
                            : ["Limited", "Stopped", "Failed"].indexOf(resultsPane.scanPhase) !== -1 ? appBridge.statusText
                            : resultsPane.scanPhase === "Complete" ? "No duplicates were found with the current filters."
                            : "Choose a folder and start a scan. Review matching files here before deciding what to remove."
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
                                id: fileRow
                                enabled: !appBridge.isCleaning
                                required property string modelData
                                property bool selected: appBridge && appBridge.previewData && appBridge.previewData.path === modelData
                                property bool deleted: appBridge ? appBridge.deletedPaths.indexOf(modelData) !== -1 : false

                                Layout.fillWidth: true
                                color: selected ? Qt.rgba(rootWindow.palette.highlight.r, rootWindow.palette.highlight.g, rootWindow.palette.highlight.b, 0.12) : (fileMouse.containsMouse ? rootWindow.mutedSurface : "transparent")
                                radius: 4
                                implicitHeight: Math.max(42, fileLabel.implicitHeight + 20)
                                activeFocusOnTab: !deleted
                                Accessible.role: Accessible.ListItem
                                Accessible.name: modelData
                                Keys.onReturnPressed: appBridge.selectPreviewFile(modelData)
                                Keys.onSpacePressed: appBridge.selectPreviewFile(modelData)
                                Keys.onDeletePressed: { if (!deleted) deleteDialog.open() }
                                border.width: activeFocus ? 2 : 0
                                border.color: rootWindow.palette.highlight

                                Label {
                                    id: fileLabel
                                    anchors.fill: parent
                                    anchors.margins: 6
                                    wrapMode: Text.WrapAnywhere
                                    font.italic: parent.deleted
                                    font.strikeout: parent.deleted
                                    color: parent.deleted
                                        ? "#b24a4a"
                                        : (parent.selected ? rootWindow.palette.link : rootWindow.palette.text)
                                    text: rootWindow.compactResultPath(modelData)
                                }

                                MouseArea {
                                    id: fileMouse
                                    hoverEnabled: true
                                    anchors.fill: parent
                                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                                    cursorShape: parent.deleted ? Qt.ArrowCursor : Qt.PointingHandCursor
                                    onClicked: function(mouse) {
                                        fileRow.forceActiveFocus()
                                        if (mouse.button === Qt.LeftButton)
                                            appBridge.selectPreviewFile(modelData)
                                        if (mouse.button === Qt.RightButton && !parent.deleted)
                                            fileMenu.popup()
                                    }
                                }

                                Menu {
                                    id: fileMenu

                                    MenuItem {
                                        text: "Move to Trash / Recycle Bin"
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
                                    title: "Move duplicate to Trash / Recycle Bin?"
                                    implicitWidth: 480
                                    width: Math.min(480, rootWindow.width - 48)
                                    parent: Overlay.overlay
                                    anchors.centerIn: parent
                                    modal: true
                                    standardButtons: Dialog.Yes | Dialog.No
                                    onAccepted: appBridge.deleteFile(modelData)

                                    contentItem: Label {
                                        wrapMode: Text.WordWrap
                                        text: "A matching copy must still exist. You can restore this file from your system's Trash / Recycle Bin.\n\n" + modelData
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
