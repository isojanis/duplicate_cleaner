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

    function formatSizeText(bytes) {
        if (bytes % (1024 * 1024 * 1024) === 0)
            return (bytes / (1024 * 1024 * 1024)) + " GB"
        if (bytes % (1024 * 1024) === 0)
            return (bytes / (1024 * 1024)) + " MB"
        if (bytes % 1024 === 0 && bytes !== 0)
            return (bytes / 1024) + " KB"
        return bytes + " B"
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
    property bool scanSummaryExpanded: true
    property string minFileSizeText: "1 B"
    property string maxFileSizeText: "1 GB"
    property string duplicateSearchLimitText: "1000"
    property string onlySearchFileExtensionText: ""
    property string newIgnoreFolderPattern: ""
    property string newIgnoreFileExtension: ""
    Component.onCompleted: {
        if (!appBridge)
            return
        root.minFileSizeText = root.formatSizeText(appBridge.minFileSizeBytes)
        root.maxFileSizeText = root.formatSizeText(appBridge.maxFileSizeBytes)
        root.duplicateSearchLimitText = String(appBridge.duplicateSearchLimit)
        root.onlySearchFileExtensionText = appBridge.onlySearchFileExtension
    }

    pageStack.initialPage: Kirigami.Page {
        title: "Duplicate Cleaner"

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing
            spacing: Kirigami.Units.smallSpacing

            Frame {
                Layout.fillWidth: true
                Layout.minimumHeight: root.scanSummaryExpanded || (appBridge && appBridge.isScanning) ? 170 : 86
                padding: 0
                background: Rectangle {
                    color: Kirigami.Theme.backgroundColor
                    radius: 12
                    border.color: Kirigami.Theme.disabledTextColor
                    border.width: 1
                }

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Kirigami.Units.smallSpacing
                    spacing: Kirigami.Units.smallSpacing

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Kirigami.Units.smallSpacing

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
                            text: appBridge && appBridge.isCancelling ? "Cancelling..." : (appBridge && appBridge.isScanning ? "Stop scan" : "Start scan")
                            highlighted: true
                            enabled: appBridge ? !appBridge.isCancelling : false
                            onClicked: appBridge.startScan()
                        }

                        ToolButton {
                            text: root.scanSummaryExpanded || (appBridge && appBridge.isScanning) ? "▴" : "▾"
                            enabled: appBridge ? !appBridge.isScanning : true
                            onClicked: root.scanSummaryExpanded = !root.scanSummaryExpanded
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

                        function onMinFileSizeBytesChanged() {
                            root.minFileSizeText = root.formatSizeText(appBridge.minFileSizeBytes)
                        }

                        function onMaxFileSizeBytesChanged() {
                            root.maxFileSizeText = root.formatSizeText(appBridge.maxFileSizeBytes)
                        }

                        function onDuplicateSearchLimitChanged() {
                            root.duplicateSearchLimitText = String(appBridge.duplicateSearchLimit)
                        }

                        function onOnlySearchFileExtensionChanged() {
                            root.onlySearchFileExtensionText = appBridge.onlySearchFileExtension
                        }
                    }

                    Connections {
                        target: appBridge

                        function onIsScanningChanged() {
                            if (appBridge.isScanning) {
                                root.scanSummaryExpanded = true
                            } else {
                                root.scanSummaryExpanded = false
                            }
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        visible: root.scanSummaryExpanded || (appBridge && appBridge.isScanning)
                        spacing: Kirigami.Units.smallSpacing

                        Flow {
                            Layout.fillWidth: true
                            spacing: Kirigami.Units.largeSpacing

                            CheckBox {
                                text: "Ignore empty files"
                                checked: appBridge ? appBridge.ignoreEmptyFiles : true
                                onToggled: if (appBridge) appBridge.setIgnoreEmptyFiles(checked)
                            }

                            CheckBox {
                                text: "Include sub-folders"
                                checked: appBridge ? appBridge.includeSubfolders : true
                                onToggled: if (appBridge) appBridge.setIncludeSubfolders(checked)
                            }

                            RowLayout {
                                spacing: Kirigami.Units.smallSpacing

                                CheckBox {
                                    text: "Limit file size range"
                                    checked: appBridge ? appBridge.limitFileSizeRange : true
                                    onToggled: if (appBridge) appBridge.setLimitFileSizeRange(checked)
                                }

                                Label { text: "Min" }

                                TextField {
                                    Layout.preferredWidth: 88
                                    enabled: appBridge ? appBridge.limitFileSizeRange : false
                                    hoverEnabled: true
                                    text: root.minFileSizeText
                                    placeholderText: "1 B"
                                    ToolTip.visible: hovered
                                    ToolTip.delay: 300
                                    ToolTip.text: "Accepts values with units like GB, MB, KB, or B. Defaults to 1 B. Example: 4 KB"
                                    onEditingFinished: if (appBridge) appBridge.setMinFileSizeText(text)
                                }

                                Label { text: "Max" }

                                TextField {
                                    Layout.preferredWidth: 88
                                    enabled: appBridge ? appBridge.limitFileSizeRange : false
                                    hoverEnabled: true
                                    text: root.maxFileSizeText
                                    placeholderText: "1 GB"
                                    ToolTip.visible: hovered
                                    ToolTip.delay: 300
                                    ToolTip.text: "Accepts values with units like GB, MB, KB, or B. Defaults to 1 GB. Example: 750 MB"
                                    onEditingFinished: if (appBridge) appBridge.setMaxFileSizeText(text)
                                }
                            }

                            RowLayout {
                                spacing: Kirigami.Units.smallSpacing

                                CheckBox {
                                    text: "Limit duplicate search"
                                    checked: appBridge ? appBridge.useDuplicateSearchLimit : true
                                    onToggled: if (appBridge) appBridge.setUseDuplicateSearchLimit(checked)
                                }

                                TextField {
                                    Layout.preferredWidth: 88
                                    enabled: appBridge ? appBridge.useDuplicateSearchLimit : false
                                    hoverEnabled: true
                                    text: root.duplicateSearchLimitText
                                    placeholderText: "1000"
                                    ToolTip.visible: hovered
                                    ToolTip.delay: 300
                                    ToolTip.text: "Stops additional hashing after this many candidate files have been hashed. Default: 1000. Example: 250"
                                    onEditingFinished: if (appBridge) appBridge.setDuplicateSearchLimitText(text)
                                }
                            }

                            RowLayout {
                                spacing: Kirigami.Units.smallSpacing

                                CheckBox {
                                    text: appBridge ? "Ignore folders (" + appBridge.ignoreFolderPatterns.length + ")" : "Ignore folders"
                                    checked: appBridge ? appBridge.useIgnoreFolderPatterns : false
                                    onToggled: if (appBridge) appBridge.setUseIgnoreFolderPatterns(checked)
                                }

                                Button {
                                    text: "Manage"
                                    enabled: appBridge ? appBridge.useIgnoreFolderPatterns : false
                                    onClicked: ignoreFoldersDialog.open()
                                }
                            }

                            RowLayout {
                                spacing: Kirigami.Units.smallSpacing

                                CheckBox {
                                    text: appBridge ? "Ignore extensions (" + appBridge.ignoreFileExtensions.length + ")" : "Ignore extensions"
                                    checked: appBridge ? appBridge.useIgnoreFileExtensions : false
                                    onToggled: if (appBridge) appBridge.setUseIgnoreFileExtensions(checked)
                                }

                                Button {
                                    text: "Manage"
                                    enabled: appBridge ? appBridge.useIgnoreFileExtensions : false
                                    onClicked: ignoreExtensionsDialog.open()
                                }
                            }

                            RowLayout {
                                spacing: Kirigami.Units.smallSpacing

                                CheckBox {
                                    text: "Only search file extension"
                                    checked: appBridge ? appBridge.useOnlySearchFileExtension : false
                                    onToggled: if (appBridge) appBridge.setUseOnlySearchFileExtension(checked)
                                }

                                TextField {
                                    Layout.preferredWidth: 100
                                    enabled: appBridge ? appBridge.useOnlySearchFileExtension : false
                                    hoverEnabled: true
                                    text: root.onlySearchFileExtensionText
                                    placeholderText: ".pdf"
                                    ToolTip.visible: hovered
                                    ToolTip.delay: 300
                                    ToolTip.text: "Restricts scanning to a single file extension. You can enter values like .pdf or pdf."
                                    onEditingFinished: if (appBridge) appBridge.setOnlySearchFileExtensionText(text)
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Kirigami.Units.largeSpacing

                            Label {
                                text: appBridge && appBridge.isScanning ? "Live scan status" : "Scan summary"
                                font.pointSize: 16
                                font.bold: true
                                Layout.alignment: Qt.AlignTop
                            }

                            Label {
                                Layout.fillWidth: true
                                Layout.alignment: Qt.AlignVCenter
                                wrapMode: Text.WordWrap
                                text: appBridge ? appBridge.statusText : "Loading..."
                            }
                        }

                        Label {
                            Layout.fillWidth: true
                            visible: root.scanSummaryExpanded && (appBridge ? appBridge.isScanning : false)
                            wrapMode: Text.WrapAnywhere
                            text: "Current path: " + (appBridge && appBridge.scanSummary ? appBridge.scanSummary.currentPath : "")
                            color: Kirigami.Theme.disabledTextColor
                        }

                        Flow {
                            Layout.fillWidth: true
                            visible: root.scanSummaryExpanded
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
                                spacing: Kirigami.Units.smallSpacing

                                Label {
                                    text: "Duplicate groups"
                                    font.pointSize: 16
                                    font.bold: true
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
                                                property bool deleted: appBridge ? appBridge.deletedPaths.indexOf(modelData) !== -1 : false

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
                                                    font.italic: parent.deleted
                                                    font.strikeout: parent.deleted
                                                    color: parent.deleted
                                                        ? "#b24a4a"
                                                        : (parent.color === "transparent"
                                                            ? Kirigami.Theme.linkColor
                                                            : Kirigami.Theme.highlightedTextColor)
                                                    text: root.compactResultPath(modelData)
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
                                                        text: "Are you sure you want to delete this file?

" + modelData
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


    Dialog {
        id: ignoreFoldersDialog
        title: "Ignore folders by pattern"
        modal: true
        width: 560
        height: Math.max(420, root.height - Kirigami.Units.gridUnit * 6)
        x: Math.round((root.width - width) / 2)
        y: Math.round((root.height - height) / 2)
        standardButtons: Dialog.Close

        onOpened: root.newIgnoreFolderPattern = ""

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
                    text: root.newIgnoreFolderPattern
                    placeholderText: "Example: /node_modules/|/.git/"
                    onTextChanged: root.newIgnoreFolderPattern = text
                    onAccepted: {
                        if (appBridge) {
                            appBridge.addIgnoreFolderPattern(text)
                            root.newIgnoreFolderPattern = ""
                            ignoreFolderPatternField.text = ""
                        }
                    }
                }

                Button {
                    text: "Add"
                    enabled: root.newIgnoreFolderPattern.trim().length > 0
                    onClicked: {
                        if (appBridge) {
                            appBridge.addIgnoreFolderPattern(root.newIgnoreFolderPattern)
                            root.newIgnoreFolderPattern = ""
                        }
                    }
                }
            }
        }
    }

    Dialog {
        id: ignoreExtensionsDialog
        title: "Ignore file extensions"
        modal: true
        width: 520
        height: Math.max(400, root.height - Kirigami.Units.gridUnit * 6)
        x: Math.round((root.width - width) / 2)
        y: Math.round((root.height - height) / 2)
        standardButtons: Dialog.Close

        onOpened: root.newIgnoreFileExtension = ""

        contentItem: ColumnLayout {
            spacing: Kirigami.Units.largeSpacing

            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: Kirigami.Theme.disabledTextColor
                text: "Files with these extensions will be skipped during scanning. You can enter values like .tmp or tmp."
            }

            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                model: appBridge ? appBridge.ignoreFileExtensions : []
                spacing: Kirigami.Units.smallSpacing

                delegate: Rectangle {
                    required property string modelData
                    width: ListView.view.width
                    radius: 8
                    color: Kirigami.Theme.alternateBackgroundColor
                    border.color: Kirigami.Theme.disabledTextColor
                    border.width: 1
                    implicitHeight: extensionRow.implicitHeight + Kirigami.Units.smallSpacing * 2

                    RowLayout {
                        id: extensionRow
                        anchors.fill: parent
                        anchors.margins: Kirigami.Units.smallSpacing
                        spacing: Kirigami.Units.smallSpacing

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
                spacing: Kirigami.Units.smallSpacing

                TextField {
                    id: ignoreFileExtensionField
                    Layout.fillWidth: true
                    text: root.newIgnoreFileExtension
                    placeholderText: "Example: .tmp"
                    onTextChanged: root.newIgnoreFileExtension = text
                    onAccepted: {
                        if (appBridge) {
                            appBridge.addIgnoreFileExtension(text)
                            root.newIgnoreFileExtension = ""
                            ignoreFileExtensionField.text = ""
                        }
                    }
                }

                Button {
                    text: "Add"
                    enabled: root.newIgnoreFileExtension.trim().length > 0
                    onClicked: {
                        if (appBridge) {
                            appBridge.addIgnoreFileExtension(root.newIgnoreFileExtension)
                            root.newIgnoreFileExtension = ""
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
