import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import org.kde.kirigami as Kirigami

Kirigami.ApplicationWindow {
    id: root

    width: 1080
    height: 720
    visible: true
    title: "Duplicate Cleaner"

    pageStack.initialPage: Kirigami.ScrollablePage {
        title: "Duplicate Cleaner"

        ColumnLayout {
            width: parent.width
            spacing: Kirigami.Units.largeSpacing

            Kirigami.InlineMessage {
                Layout.fillWidth: true
                text: "Starter UI for a KDE-friendly duplicate finder."
                type: Kirigami.MessageType.Information
                visible: true
            }

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

                    TextField {
                        Layout.fillWidth: true
                        readOnly: true
                        text: appBridge.selectedFolder
                    }

                    RowLayout {
                        Button {
                            text: "Choose folder"
                            onClicked: folderDialog.open()
                        }

                        Button {
                            text: "Start scan"
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
                implicitHeight: resultsColumn.implicitHeight + Kirigami.Units.largeSpacing * 2

                ColumnLayout {
                    id: resultsColumn
                    anchors.fill: parent
                    anchors.margins: Kirigami.Units.largeSpacing
                    spacing: Kirigami.Units.smallSpacing

                    Label {
                        text: "Status"
                        font.pointSize: 16
                        font.bold: true
                    }

                    Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        text: appBridge.statusText
                    }

                    Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        text: "Next step: wire the scanner backend and show duplicate groups in this panel."
                        color: Kirigami.Theme.disabledTextColor
                    }
                }
            }
        }
    }

    FolderDialog {
        id: folderDialog
        currentFolder: "file://" + appBridge.selectedFolder
        onAccepted: appBridge.setSelectedFolder(selectedFolder.toString())
    }
}
