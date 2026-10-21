# Windows portable build testing

These steps test the application on Windows 10/11 x64. The output is an
unreviewed engineering build, not a cleared public release. See
[LICENSE_AUDIT.md](LICENSE_AUDIT.md) for the separate license review.

## Build

Install Python 3.13 x64 and open PowerShell in the repository root. Activation
is optional; these commands do not require changing PowerShell execution policy:

```powershell
py -3.13 -m venv .venv-build
.\.venv-build\Scripts\python -m pip install -r packaging\windows\requirements-build.txt
.\packaging\windows\build.ps1 -Python .\.venv-build\Scripts\python.exe
```

The script creates `dist/DuplicateCleaner-0.1.0-windows-x64-unreviewed.zip` and
its `.sha256` sidecar. It verifies the checksum and required application and
license files, then extracts and starts the app from a temporary path containing
spaces and Unicode. This verifies startup, not licensing completeness.

## Manual acceptance

Extract the whole ZIP outside the checkout and launch `DuplicateCleaner.exe`.
Use disposable fixture files for every cleanup check.

- Check the window, taskbar icon, keyboard navigation, and scaling.
- Select a folder with nested duplicates; verify counts, progress, and filters.
- Stop a large scan using the button and Escape; confirm partial-result status.
- Preview text, PNG/JPEG, and PDF files with spaces and Unicode in their paths.
- Move one duplicate to the Recycle Bin; the UI should mark it as removed.
  Restore it through Explorer and compare its bytes with the retained copy.
- Modify a duplicate after scanning and confirm cleanup refuses stale evidence.
- Check an empty folder, an unavailable folder, and a UNC path where available.

Record the Windows version, Python patch version, package checksum, results,
and any skipped checks. CI currently builds and tests Windows bundles but does
not upload them while the binary license audit remains incomplete.

## Validate an existing test archive

Keep the `.sha256` beside the ZIP and run:

```powershell
.\packaging\windows\validate-portable.ps1 -Archive .\dist\DuplicateCleaner-0.1.0-windows-x64-unreviewed.zip
```

For startup failures, retain the validator output and Windows Event Viewer
application error. A timeout needs investigation; it is not proof of a graphics
problem. Report QML warnings with the affected file and message.
