import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Pdf
import org.kde.kirigami as Kirigami

Frame {
    property var rootWindow

    SplitView.preferredWidth: 560
    SplitView.minimumWidth: 400
    SplitView.maximumWidth: 840
    padding: 0
    background: Rectangle {
        color: Kirigami.Theme.backgroundColor
        radius: 8
        border.color: Kirigami.Theme.disabledTextColor
        border.width: 1
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Kirigami.Units.smallSpacing
        spacing: Kirigami.Units.smallSpacing

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
            font.italic: appBridge && appBridge.previewData ? appBridge.previewData.isDeleted : false
            font.strikeout: appBridge && appBridge.previewData ? appBridge.previewData.isDeleted : false
            color: appBridge && appBridge.previewData && appBridge.previewData.isDeleted ? "#b24a4a" : Kirigami.Theme.textColor
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
            Label { text: rootWindow.formatBytes(appBridge && appBridge.previewData ? appBridge.previewData.sizeBytes : 0) }
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
            radius: 8
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
}
