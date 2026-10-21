param([Parameter(Mandatory = $true)][string]$Archive)

$ErrorActionPreference = 'Stop'
$Archive = (Resolve-Path -LiteralPath $Archive).Path
$Expected = (Get-Content -LiteralPath "$Archive.sha256" -Raw).Trim()
$Actual = (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant()
if ($Expected -cne "$Actual  $([IO.Path]::GetFileName($Archive))") {
    throw 'Portable archive SHA-256 checksum does not match.'
}

# Exercise extraction and launch from a path with spaces and Unicode outside the checkout.
$TempRoot = Join-Path ([IO.Path]::GetTempPath()) ("duplicate cleaner caf$([char]0x00e9) " + [guid]::NewGuid())
$Process = $null
$SavedEnvironment = @{}
try {
    Expand-Archive -LiteralPath $Archive -DestinationPath $TempRoot
    $AppRoot = Join-Path $TempRoot 'DuplicateCleaner'
    foreach ($RelativePath in @(
        'DuplicateCleaner.exe',
        '_internal/LICENSE',
        '_internal/THIRD_PARTY_NOTICES',
        '_internal/README.md',
        '_internal/duplicate_cleaner/resources/qml/Main.qml',
        '_internal/duplicate_cleaner/resources/qml/components/ResultsPane.qml',
        '_internal/duplicate_cleaner/resources/assets/duplicate-cleaner.svg'
    )) {
        if (-not (Test-Path -LiteralPath (Join-Path $AppRoot $RelativePath) -PathType Leaf)) {
            throw "The extracted portable archive is missing $RelativePath."
        }
    }
    if ($env:OS -ne 'Windows_NT') { throw 'Executable validation requires native Windows.' }
    foreach ($Name in @('PYTHONPATH', 'PYTHONHOME', 'QML_IMPORT_PATH', 'QML2_IMPORT_PATH', 'QT_PLUGIN_PATH', 'QT_QPA_PLATFORM_PLUGIN_PATH')) {
        $SavedEnvironment[$Name] = [Environment]::GetEnvironmentVariable($Name, 'Process')
        [Environment]::SetEnvironmentVariable($Name, $null, 'Process')
    }
    $App = Join-Path $AppRoot 'DuplicateCleaner.exe'
    $Process = Start-Process -FilePath $App -ArgumentList '--smoke-test' -WorkingDirectory $TempRoot -PassThru
    $null = $Process.Handle
    if (-not $Process.WaitForExit(60000)) { throw 'Extracted executable smoke test timed out.' }
    if ($Process.ExitCode -ne 0) { throw "Extracted executable smoke test failed: exit $($Process.ExitCode)." }
    Write-Host 'Portable archive checksum, contents, and extracted executable startup passed.'
} finally {
    if ($null -ne $Process) {
        if (-not $Process.HasExited) {
            $Process.Kill()
            $null = $Process.WaitForExit(5000)
        }
        $Process.Dispose()
    }
    foreach ($Name in $SavedEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($Name, $SavedEnvironment[$Name], 'Process')
    }
    if (Test-Path -LiteralPath $TempRoot) { Remove-Item -LiteralPath $TempRoot -Recurse -Force }
}
