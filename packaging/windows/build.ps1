param([string]$Python = 'python')

$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Build the Windows executable on Windows.' }

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Push-Location $ProjectRoot
try {
    # Feed Python through stdin to preserve quotes in Windows PowerShell 5.1 too.
    $BuildInfoJson = @'
import json, sys, sysconfig, tomllib
with open("pyproject.toml", "rb") as stream:
    version = tomllib.load(stream)["project"]["version"]
print(json.dumps(dict(version=version, python=list(sys.version_info[:2]), platform=sysconfig.get_platform())))
'@ | & $Python -
    if ($LASTEXITCODE -ne 0) { throw 'Could not read the Python and project build information.' }
    $BuildInfo = $BuildInfoJson | ConvertFrom-Json
    if (($BuildInfo.python -join '.') -ne '3.13' -or $BuildInfo.platform -ne 'win-amd64') {
        throw 'Use x64 Python 3.13 for the Windows x64 portable build.'
    }
    $Version = $BuildInfo.version

    & $Python -m PyInstaller --noconfirm --clean packaging/windows/duplicate-cleaner.spec
    if ($LASTEXITCODE -ne 0) { throw 'Executable build failed.' }
    $App = Join-Path $ProjectRoot 'dist/DuplicateCleaner/DuplicateCleaner.exe'
    if (-not (Test-Path $App)) { throw 'The executable was not created.' }

    $ArtifactName = "DuplicateCleaner-$Version-windows-x64"
    $Archive = Join-Path $ProjectRoot "dist/$ArtifactName.zip"
    Compress-Archive -Path 'dist/DuplicateCleaner' -DestinationPath $Archive -Force

    $Checksum = Get-FileHash -Path $Archive -Algorithm SHA256
    "$($Checksum.Hash.ToLowerInvariant())  $ArtifactName.zip" |
        Set-Content -Path "$Archive.sha256" -Encoding ascii
    & (Join-Path $PSScriptRoot 'validate-portable.ps1') -Archive $Archive
    Write-Host "Portable build: $Archive"
    Write-Host "SHA-256: $Archive.sha256"
} finally {
    Pop-Location
}
