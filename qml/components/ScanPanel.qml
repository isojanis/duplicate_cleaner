import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Frame {
    id: scanPanel

    property var rootWindow
    property var folderDialog
    property var ignoreFoldersDialog
    property var ignoreExtensionsDialog
    property string minFileSizeText: "1 B"
    property string maxFileSizeText: "1 GB"
    property string duplicateSearchLimitText: "1000"
    property string onlySearchFileExtensionText: ""

    Layout.fillWidth: true
    Layout.minimumHeight: rootWindow.scanSummaryExpanded || (appBridge && appBridge.isScanning) ? 156 : 76
    padding: 0
    background: Rectangle {
        color: Kirigami.Theme.backgroundColor
        radius: 8
        border.color: Kirigami.Theme.disabledTextColor
        border.width: 1
    }

    Component.onCompleted: {
        if (!appBridge)
            return
        minFileSizeText = rootWindow.formatSizeText(appBridge.minFileSizeBytes)
        maxFileSizeText = rootWindow.formatSizeText(appBridge.maxFileSizeBytes)
        duplicateSearchLimitText = String(appBridge.duplicateSearchLimit)
        onlySearchFileExtensionText = appBridge.onlySearchFileExtension
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Kirigami.Units.smallSpacing / 2
        spacing: Kirigami.Units.smallSpacing / 2

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
                text: rootWindow.scanSummaryExpanded || (appBridge && appBridge.isScanning) ? "▴" : "▾"
                enabled: appBridge ? !appBridge.isScanning : true
                onClicked: rootWindow.scanSummaryExpanded = !rootWindow.scanSummaryExpanded
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
                scanPanel.minFileSizeText = rootWindow.formatSizeText(appBridge.minFileSizeBytes)
            }

            function onMaxFileSizeBytesChanged() {
                scanPanel.maxFileSizeText = rootWindow.formatSizeText(appBridge.maxFileSizeBytes)
            }

            function onDuplicateSearchLimitChanged() {
                scanPanel.duplicateSearchLimitText = String(appBridge.duplicateSearchLimit)
            }

            function onOnlySearchFileExtensionChanged() {
                scanPanel.onlySearchFileExtensionText = appBridge.onlySearchFileExtension
            }

            function onIsScanningChanged() {
                rootWindow.scanSummaryExpanded = appBridge.isScanning
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            visible: rootWindow.scanSummaryExpanded || (appBridge && appBridge.isScanning)
            spacing: Kirigami.Units.smallSpacing

            GridLayout {
                Layout.fillWidth: true
                columns: 2
                columnSpacing: Kirigami.Units.largeSpacing
                rowSpacing: Kirigami.Units.smallSpacing

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing

                    CheckBox {
                        text: "Ignore empty files"
                        checked: appBridge ? appBridge.ignoreEmptyFiles : true
                        onToggled: if (appBridge) appBridge.setIgnoreEmptyFiles(checked)
                    }

                    Item { Layout.fillWidth: true }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing

                    CheckBox {
                        text: "Include sub-folders"
                        checked: appBridge ? appBridge.includeSubfolders : true
                        onToggled: if (appBridge) appBridge.setIncludeSubfolders(checked)
                    }

                    Item { Layout.fillWidth: true }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing

                    CheckBox {
                        text: "Limit file size range"
                        checked: appBridge ? appBridge.limitFileSizeRange : true
                        onToggled: if (appBridge) appBridge.setLimitFileSizeRange(checked)
                    }

                    Label { text: "Min" }

                    TextField {
                        Layout.preferredWidth: 84
                        enabled: appBridge ? appBridge.limitFileSizeRange : false
                        hoverEnabled: true
                        text: scanPanel.minFileSizeText
                        placeholderText: "1 B"
                        ToolTip.visible: hovered
                        ToolTip.delay: 300
                        ToolTip.text: "Accepts values with units like GB, MB, KB, or B. Defaults to 1 B. Example: 4 KB"
                        onEditingFinished: if (appBridge) appBridge.setMinFileSizeText(text)
                    }

                    Label { text: "Max" }

                    TextField {
                        Layout.preferredWidth: 84
                        enabled: appBridge ? appBridge.limitFileSizeRange : false
                        hoverEnabled: true
                        text: scanPanel.maxFileSizeText
                        placeholderText: "1 GB"
                        ToolTip.visible: hovered
                        ToolTip.delay: 300
                        ToolTip.text: "Accepts values with units like GB, MB, KB, or B. Defaults to 1 GB. Example: 750 MB"
                        onEditingFinished: if (appBridge) appBridge.setMaxFileSizeText(text)
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing

                    CheckBox {
                        text: "Limit duplicate search"
                        checked: appBridge ? appBridge.useDuplicateSearchLimit : true
                        onToggled: if (appBridge) appBridge.setUseDuplicateSearchLimit(checked)
                    }

                    TextField {
                        Layout.preferredWidth: 84
                        enabled: appBridge ? appBridge.useDuplicateSearchLimit : false
                        hoverEnabled: true
                        text: scanPanel.duplicateSearchLimitText
                        placeholderText: "1000"
                        ToolTip.visible: hovered
                        ToolTip.delay: 300
                        ToolTip.text: "Stops additional hashing after this many candidate files have been hashed. Default: 1000. Example: 250"
                        onEditingFinished: if (appBridge) appBridge.setDuplicateSearchLimitText(text)
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
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

                    Item { Layout.fillWidth: true }
                }

                RowLayout {
                    Layout.fillWidth: true
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

                    Item { Layout.fillWidth: true }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing

                    CheckBox {
                        text: "Only search file extension"
                        checked: appBridge ? appBridge.useOnlySearchFileExtension : false
                        onToggled: if (appBridge) appBridge.setUseOnlySearchFileExtension(checked)
                    }

                    TextField {
                        Layout.preferredWidth: 96
                        enabled: appBridge ? appBridge.useOnlySearchFileExtension : false
                        hoverEnabled: true
                        text: scanPanel.onlySearchFileExtensionText
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
                spacing: Kirigami.Units.smallSpacing

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
                visible: rootWindow.scanSummaryExpanded && (appBridge ? appBridge.isScanning : false)
                wrapMode: Text.WrapAnywhere
                text: "Current path: " + (appBridge && appBridge.scanSummary ? appBridge.scanSummary.currentPath : "")
                color: Kirigami.Theme.disabledTextColor
            }

            GridLayout {
                id: liveScanStatsGrid
                Layout.fillWidth: true
                visible: rootWindow.scanSummaryExpanded
                columns: Math.max(1, Math.min(statRepeater.count, Math.floor((width + columnSpacing) / 170)))
                columnSpacing: Kirigami.Units.smallSpacing
                rowSpacing: Kirigami.Units.smallSpacing

                Repeater {
                    id: statRepeater
                    model: [
                        { label: "Files scanned", value: String(appBridge && appBridge.scanSummary ? appBridge.scanSummary.totalFiles : 0) },
                        { label: "Folders scanned", value: String(appBridge && appBridge.scanSummary ? appBridge.scanSummary.totalFolders : 0) },
                        { label: "Skipped unreadable", value: String(appBridge && appBridge.scanSummary ? appBridge.scanSummary.skippedFiles : 0) },
                        { label: "Duplicate groups", value: String(appBridge && appBridge.scanSummary ? appBridge.scanSummary.groupCount : 0) },
                        { label: "Duplicate files", value: String(appBridge && appBridge.scanSummary ? appBridge.scanSummary.duplicateFiles : 0) },
                        { label: "Hash progress", value: appBridge && appBridge.scanSummary ? String(appBridge.scanSummary.hashedFiles) + " / " + String(appBridge.scanSummary.hashCandidates) : "0 / 0" },
                        { label: "Wasted space", value: rootWindow.formatBytes(appBridge && appBridge.scanSummary ? appBridge.scanSummary.wastedBytes : 0) }
                    ]

                    delegate: Rectangle {
                        required property var modelData

                        Layout.fillWidth: true
                        Layout.preferredWidth: Math.max(140, (liveScanStatsGrid.width - liveScanStatsGrid.columnSpacing * Math.max(0, liveScanStatsGrid.columns - 1)) / liveScanStatsGrid.columns)
                        implicitHeight: statsColumn.implicitHeight + Kirigami.Units.smallSpacing * 2
                        radius: 6
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
