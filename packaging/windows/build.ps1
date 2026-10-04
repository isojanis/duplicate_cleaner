$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Push-Location $ProjectRoot
try {
    python -m PyInstaller --noconfirm --clean packaging/windows/duplicate-cleaner.spec
    if ($LASTEXITCODE -ne 0) { throw 'Executable build failed.' }
    $App = Join-Path $ProjectRoot 'dist/DuplicateCleaner/DuplicateCleaner.exe'
    $Process = Start-Process -FilePath $App -ArgumentList '--smoke-test' -PassThru
    if (-not $Process.WaitForExit(60000)) {
        $Process.Kill()
        throw 'Executable smoke test timed out.'
    }
    if ($Process.ExitCode -ne 0) { throw 'Executable smoke test failed.' }
    Compress-Archive -Path 'dist/DuplicateCleaner' -DestinationPath 'dist/DuplicateCleaner-windows-x64.zip' -Force
    Write-Host 'Portable build: dist/DuplicateCleaner-windows-x64.zip'
} finally {
    Pop-Location
}
