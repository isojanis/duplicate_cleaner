import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Pdf

Frame {
    property var rootWindow
    readonly property bool hasSelection: !!(appBridge && appBridge.previewData && appBridge.previewData.path)

    SplitView.preferredWidth: 350
    SplitView.minimumWidth: 300
    SplitView.maximumWidth: 600
    padding: 0
    background: Rectangle {
        color: rootWindow.palette.base
        radius: 12
        border.color: rootWindow.subtleBorder
        border.width: 1
    }

    ScrollView {
        id: previewScroll
        anchors.fill: parent
        anchors.margins: 20
        clip: true
        contentWidth: availableWidth

    ColumnLayout {
        width: previewScroll.availableWidth
        spacing: 12

        RowLayout {
            Layout.fillWidth: true

            Label {
                text: "Preview"
                font.pixelSize: 18
                font.bold: true
            }

            Item { Layout.fillWidth: true }

            ActionButton {
                text: "Show in folder"
                icon.name: "folder-open"
                visible: hasSelection
                enabled: appBridge && appBridge.previewData && appBridge.previewData.path !== ""
                onClicked: appBridge.openPreviewFolder()
            }
        }

        Label {
            Layout.fillWidth: true
            visible: hasSelection
            wrapMode: Text.WordWrap
            font.bold: true
            font.italic: appBridge && appBridge.previewData ? appBridge.previewData.isDeleted : false
            font.strikeout: appBridge && appBridge.previewData ? appBridge.previewData.isDeleted : false
            color: appBridge && appBridge.previewData && appBridge.previewData.isDeleted ? "#b24a4a" : rootWindow.palette.text
            text: appBridge && appBridge.previewData ? appBridge.previewData.name : "No file selected"
        }

        Label {
            Layout.fillWidth: true
            visible: hasSelection
            wrapMode: Text.WrapAnywhere
            color: rootWindow.mutedText
            text: appBridge && appBridge.previewData ? appBridge.previewData.path : ""
        }

        GridLayout {
            Layout.fillWidth: true
            visible: hasSelection
            columns: 2
            columnSpacing: 12
            rowSpacing: 6

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
            color: rootWindow.mutedText
            visible: hasSelection
            text: appBridge && appBridge.previewData ? appBridge.previewData.statusText : ""
        }

        Label {
            Layout.fillWidth: true
            visible: appBridge && appBridge.previewData ? appBridge.previewData.isTruncated : false
            wrapMode: Text.WordWrap
            color: rootWindow.mutedText
            text: "Preview truncated for large text files."
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: Math.max(180, previewScroll.availableHeight - 250)
            color: rootWindow.mutedSurface
            radius: 12
            border.color: rootWindow.subtleBorder
            border.width: 0
            clip: true

            Loader {
                anchors.fill: parent
                anchors.margins: 6
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
            ColumnLayout {
                anchors.centerIn: parent
                width: Math.min(parent.width - 32, 260)
                spacing: 12
                Label {
                    text: "▤"
                    font.pixelSize: 36
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: 40
                    Layout.preferredHeight: 40
                    opacity: 0.4
                    visible: parent.parent.height > 180
                }
                Label {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                    text: hasSelection ? "Preview unavailable" : "Take a closer look"
                }
                Label {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    color: rootWindow.mutedText
                    text: hasSelection ? appBridge.previewData.textContent : "Select a file in the results to inspect its contents and details."
                }
            }
        }
    }
}
