$ErrorActionPreference = 'Stop'
$PythonInfo = python -c 'import platform, sys; print(f"{sys.version_info.major}.{sys.version_info.minor};{platform.architecture()[0]}")'
if ($LASTEXITCODE -ne 0) { throw 'Could not inspect the active Python interpreter.' }
if ($env:OS -ne 'Windows_NT') { throw 'Build the Windows executable on Windows.' }
if ($PythonInfo -ne '3.13;64bit') {
    throw "Use 64-bit Python 3.13 for the portable build (found $PythonInfo)."
}

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Push-Location $ProjectRoot
try {
    $Version = python -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])'
    if ($LASTEXITCODE -ne 0 -or -not $Version) { throw 'Could not read the project version from pyproject.toml.' }

    python -m PyInstaller --noconfirm --clean packaging/windows/duplicate-cleaner.spec
    if ($LASTEXITCODE -ne 0) { throw 'Executable build failed.' }
    $App = Join-Path $ProjectRoot 'dist/DuplicateCleaner/DuplicateCleaner.exe'
    if (-not (Test-Path $App)) { throw 'The executable was not created.' }

    $Process = Start-Process -FilePath $App -ArgumentList '--smoke-test' -PassThru
    if (-not $Process.WaitForExit(60000)) {
        $Process.Kill()
        $Process.WaitForExit()
        throw 'Executable smoke test timed out.'
    }
    if ($Process.ExitCode -ne 0) { throw 'Executable smoke test failed.' }

    $ArtifactName = "DuplicateCleaner-$Version-windows-x64"
    $Archive = Join-Path $ProjectRoot "dist/$ArtifactName.zip"
    Compress-Archive -Path 'dist/DuplicateCleaner' -DestinationPath $Archive -Force

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $Zip = [System.IO.Compression.ZipFile]::OpenRead($Archive)
    try {
        foreach ($RequiredFile in @('LICENSE', 'README.md')) {
            if (-not ($Zip.Entries | Where-Object { $_.FullName -match "(^|/)$RequiredFile$" })) {
                throw "The portable archive is missing $RequiredFile."
            }
        }
    } finally {
        $Zip.Dispose()
    }

    $Checksum = Get-FileHash -Path $Archive -Algorithm SHA256
    "$($Checksum.Hash.ToLowerInvariant())  $ArtifactName.zip" |
        Set-Content -Path "$Archive.sha256" -Encoding ascii
    Write-Host "Portable build: $Archive"
    Write-Host "SHA-256: $Archive.sha256"
} finally {
    Pop-Location
}
