import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Dialog {
    id: dialog

    property var rootWindow

    title: "Ignore file extensions"
    modal: true
    width: 520
    height: Math.max(400, rootWindow.height - 18 * 6)
    x: Math.round((rootWindow.width - width) / 2)
    y: Math.round((rootWindow.height - height) / 2)
    standardButtons: Dialog.Close

    onOpened: ignoreFileExtensionField.text = ""

    contentItem: ColumnLayout {
        spacing: 12

        Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: rootWindow.palette.placeholderText
            text: "Files with these extensions will be skipped during scanning. You can enter values like .tmp or tmp."
        }

        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: appBridge ? appBridge.ignoreFileExtensions : []
            spacing: 6

            delegate: Rectangle {
                required property string modelData
                width: ListView.view.width
                radius: 8
                color: rootWindow.palette.alternateBase
                border.color: rootWindow.palette.placeholderText
                border.width: 1
                implicitHeight: extensionRow.implicitHeight + 6 * 2

                RowLayout {
                    id: extensionRow
                    anchors.fill: parent
                    anchors.margins: 6
                    spacing: 6

                    Label {
                        Layout.fillWidth: true
                        text: modelData
                    }

                    Button {
                        text: "Remove"
                        onClicked: if (appBridge) appBridge.removeIgnoreFileExtension(modelData)
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            TextField {
                id: ignoreFileExtensionField
                Layout.fillWidth: true
                placeholderText: "Example: .tmp"
                onAccepted: {
                    if (appBridge && text.trim().length > 0) {
                        appBridge.addIgnoreFileExtension(text)
                        text = ""
                    }
                }
            }

            Button {
                text: "Add"
                enabled: ignoreFileExtensionField.text.trim().length > 0
                onClicked: {
                    if (appBridge) {
                        appBridge.addIgnoreFileExtension(ignoreFileExtensionField.text)
                        ignoreFileExtensionField.text = ""
                    }
                }
            }
        }
    }
}
