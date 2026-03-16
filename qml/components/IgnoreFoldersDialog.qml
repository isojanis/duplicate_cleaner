import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Dialog {
    id: dialog

    property var rootWindow

    title: "Ignore folders by pattern"
    modal: true
    width: 560
    height: Math.max(420, rootWindow.height - Kirigami.Units.gridUnit * 6)
    x: Math.round((rootWindow.width - width) / 2)
    y: Math.round((rootWindow.height - height) / 2)
    standardButtons: Dialog.Close

    onOpened: ignoreFolderPatternField.text = ""

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: Kirigami.Theme.disabledTextColor
            text: "Folder paths matching any of these regular expressions will be skipped during scanning."
        }

        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: appBridge ? appBridge.ignoreFolderPatterns : []
            spacing: Kirigami.Units.smallSpacing

            delegate: Rectangle {
                required property string modelData
                width: ListView.view.width
                radius: 8
                color: Kirigami.Theme.alternateBackgroundColor
                border.color: Kirigami.Theme.disabledTextColor
                border.width: 1
                implicitHeight: patternRow.implicitHeight + Kirigami.Units.smallSpacing * 2

                RowLayout {
                    id: patternRow
                    anchors.fill: parent
                    anchors.margins: Kirigami.Units.smallSpacing
                    spacing: Kirigami.Units.smallSpacing

                    Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WrapAnywhere
                        text: modelData
                    }

                    Button {
                        text: "Remove"
                        onClicked: if (appBridge) appBridge.removeIgnoreFolderPattern(modelData)
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing

            TextField {
                id: ignoreFolderPatternField
                Layout.fillWidth: true
                placeholderText: "Example: /node_modules/|/.git/"
                onAccepted: {
                    if (appBridge && text.trim().length > 0) {
                        appBridge.addIgnoreFolderPattern(text)
                        text = ""
                    }
                }
            }

            Button {
                text: "Add"
                enabled: ignoreFolderPatternField.text.trim().length > 0
                onClicked: {
                    if (appBridge) {
                        appBridge.addIgnoreFolderPattern(ignoreFolderPatternField.text)
                        ignoreFolderPatternField.text = ""
                    }
                }
            }
        }
    }
}
