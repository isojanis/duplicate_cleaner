import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

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
    implicitHeight: scanContent.implicitHeight + 40
    padding: 0
    background: Rectangle {
        color: rootWindow.palette.base
        radius: 12
        border.color: rootWindow.subtleBorder
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
        id: scanContent
        anchors.fill: parent
        anchors.margins: 20
        spacing: 14

        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Label {
                text: "Folder"
                font.pixelSize: 14
                font.bold: true
            }

            ComboBox {
                id: folderField
                objectName: "folderField"
                Layout.preferredHeight: 40
                Layout.fillWidth: true
                editable: true
                enabled: appBridge ? !appBridge.isScanning && !appBridge.isCleaning : false
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

            ActionButton {
                text: "Browse…"
                icon.name: "folder-open"
                enabled: appBridge ? !appBridge.isScanning && !appBridge.isCleaning : false
                onClicked: folderDialog.open()
            }

            ActionButton {
                text: appBridge && appBridge.isCancelling ? "Cancelling..." : (appBridge && appBridge.isScanning ? "Stop scan" : "Start scan")
                objectName: "scanButton"
                icon.name: appBridge && appBridge.isScanning ? "process-stop" : "edit-find"
                Layout.preferredHeight: 40
                highlighted: true
                enabled: appBridge ? !appBridge.isCancelling && !appBridge.isCleaning : false
                onClicked: {
                    if (!appBridge.isScanning)
                        appBridge.setSelectedFolder(folderField.editText)
                    appBridge.startScan()
                }
            }

        }

        RowLayout {
            Layout.fillWidth: true
            ActionButton {
                text: "Stop cleanup"
                visible: appBridge && appBridge.isCleaning
                onClicked: appBridge.stopCleanup()
            }
            Label {
                Layout.fillWidth: true
                text: appBridge ? appBridge.statusText : "Choose a folder to begin."
                wrapMode: Text.WordWrap
                color: rootWindow.mutedText
            }
            ToolButton {
                objectName: "optionsButton"
                text: rootWindow.scanSummaryExpanded ? "Hide filters" : "Scan filters"
                icon.name: "configure"
                checkable: true
                checked: rootWindow.scanSummaryExpanded
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


        }

        ColumnLayout {
            Layout.fillWidth: true
            visible: rootWindow.scanSummaryExpanded
            spacing: 6

            GridLayout {
                Layout.fillWidth: true
                enabled: appBridge ? !appBridge.isScanning : false
                columns: width > 1000 ? 3 : 2
                columnSpacing: 12
                rowSpacing: 6

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    CheckBox {
                        text: "Ignore empty files"
                        checked: appBridge ? appBridge.ignoreEmptyFiles : true
                        onToggled: if (appBridge) appBridge.setIgnoreEmptyFiles(checked)
                    }

                    Item { Layout.fillWidth: true }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    CheckBox {
                        text: "Include sub-folders"
                        checked: appBridge ? appBridge.includeSubfolders : true
                        onToggled: if (appBridge) appBridge.setIncludeSubfolders(checked)
                    }

                    Item { Layout.fillWidth: true }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6

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
                    spacing: 6

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
                    spacing: 6

                    CheckBox {
                        text: appBridge ? "Ignore folders (" + appBridge.ignoreFolderPatterns.length + ")" : "Ignore folders"
                        checked: appBridge ? appBridge.useIgnoreFolderPatterns : false
                        onToggled: if (appBridge) appBridge.setUseIgnoreFolderPatterns(checked)
                    }

                    ActionButton {
                        text: "Manage"
                        enabled: appBridge ? appBridge.useIgnoreFolderPatterns : false
                        onClicked: ignoreFoldersDialog.open()
                    }

                    Item { Layout.fillWidth: true }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    CheckBox {
                        text: appBridge ? "Ignore extensions (" + appBridge.ignoreFileExtensions.length + ")" : "Ignore extensions"
                        checked: appBridge ? appBridge.useIgnoreFileExtensions : false
                        onToggled: if (appBridge) appBridge.setUseIgnoreFileExtensions(checked)
                    }

                    ActionButton {
                        text: "Manage"
                        enabled: appBridge ? appBridge.useIgnoreFileExtensions : false
                        onClicked: ignoreExtensionsDialog.open()
                    }

                    Item { Layout.fillWidth: true }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6

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

        }

        ProgressBar {
            Layout.fillWidth: true
            visible: appBridge && appBridge.isScanning
            indeterminate: !appBridge || !appBridge.scanSummary.hashCandidates
            from: 0
            to: appBridge && appBridge.scanSummary ? Math.max(1, appBridge.scanSummary.hashWorkCandidates) : 1
            value: appBridge && appBridge.scanSummary
                ? appBridge.scanSummary.hashCandidatesProcessed
                    + (appBridge.scanSummary.currentFileSize > 0
                        ? appBridge.scanSummary.currentFileBytes / appBridge.scanSummary.currentFileSize
                        : 0)
                : 0
        }
        Label {
            Layout.fillWidth: true
            visible: appBridge && appBridge.isScanning
            text: appBridge && appBridge.scanSummary ? appBridge.scanSummary.currentPath : ""
            elide: Text.ElideMiddle
            font.pixelSize: 11
            color: rootWindow.mutedText
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 20
            Repeater {
                model: [
                    { label: "Files scanned", value: String(appBridge && appBridge.scanSummary ? appBridge.scanSummary.totalFiles : 0) },
                    { label: "Duplicate groups", value: String(appBridge && appBridge.scanSummary ? appBridge.scanSummary.groupCount : 0) },
                    { label: "Extra copies", value: String(appBridge && appBridge.scanSummary ? Math.max(0, appBridge.scanSummary.duplicateFiles - appBridge.scanSummary.groupCount) : 0) },
                    { label: "Reclaimable space", value: rootWindow.formatBytes(appBridge && appBridge.scanSummary ? appBridge.scanSummary.wastedBytes : 0) }
                ]
                delegate: Rectangle {
                    required property var modelData
                    Layout.fillWidth: true
                    implicitHeight: 74
                    color: rootWindow.mutedSurface
                    radius: 8
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 3
                        Label { text: modelData.value; font.pixelSize: 22; font.weight: Font.DemiBold }
                        Label { text: modelData.label; font.pixelSize: 12; color: rootWindow.mutedText }
                    }
                }
            }
        }
        Label {
            Layout.fillWidth: true
            visible: appBridge && appBridge.scanSummary && appBridge.scanSummary.skippedFiles > 0
            text: appBridge && appBridge.scanSummary ? appBridge.scanSummary.skippedFiles + " unavailable, changed, or non-regular entries skipped" : ""
            color: rootWindow.mutedText
            font.pixelSize: 11
        }
    }
}
