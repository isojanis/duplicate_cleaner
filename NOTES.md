# Duplicate Cleaner — Project Notes

Last reviewed: 2026-10-04

## Current status

The project is a functional prototype rather than a UI-only scaffold.

Implemented:

- Duplicate scanning by file size and SHA-256 content hash.
- Recursive scanning with cancellation and progress reporting.
- File filters for empty files, size range, extensions, folder regexes, and a single extension.
- Persistent scan preferences and recent folders through `QSettings`.
- Duplicate results grouped by matching content, with reclaimable-space summaries.
- Text, image, and PDF preview handling.
- Individual file deletion with confirmation and deleted-state updates.
- Smart cleanup for same-folder filename/hash candidates.
- Qt Quick interface with scan, results, preview, filter, and cleanup panels; KDE/Kirigami is not required.
- Recoverable deletion through the system Trash / Windows Recycle Bin, with asynchronous revalidation and cancellation.
- Live scan status distinguishes candidate discovery from hashing and reports byte progress within large files.
- Portable wheel and PyInstaller build recipes for Windows and Linux smoke validation.
- Windows portable build emits a versioned ZIP and SHA-256 sidecar; its archive includes README and LICENSE.
- RPM packaging metadata and desktop integration.

## Verification completed

- `python3 -m compileall -q src tests packaging/windows/launcher.py` passes.
- 21 regression tests pass, including scanner, bridge, cleanup-worker, live hash progress, and full QML loading tests.
- The suite passes with both the isolated PySide6 environment and native Fedora Qt packages.
- The built wheel contains the full QML tree and icon and launches outside the source checkout.
- The PyInstaller recipe builds and its Linux frozen executable startup smoke test passes.
- The minimum 960×680 UI was visually checked; the preview pane scrolls and populated results load without QML warnings.

## Known gaps

- RPM build validation is pending because the native Fedora host lacks `pyproject-rpm-macros`, `python3-build`, and the RPM build dependency set. The build helper now checks for its local build tool and writes package artifacts under `dist/rpm/`.
- `LICENSE` is an MIT template with placeholder year and copyright holder; complete those fields before distribution.
- Native Windows execution and acceptance testing are pending.
- The updated Windows ZIP, checksum, and executable icon path were not run locally; this Fedora host has no PowerShell or PyInstaller. The Windows CI job must validate the build script.
- Review licenses/notices for bundled PySide6/Qt and other third-party components before distributing the Windows archive.
- GitHub Actions has been added but has not run from this workspace.
- Local generated output may still appear from earlier builds; `build/`, `dist/`, `*.egg-info/`, caches, and temporary virtual environments are now ignored for future builds.
- The ignored wheel currently in `dist/` is stale and does not contain the packaged QML or icon; rebuild it before using that artifact for validation.

## Next-step plan

### 1. Make packaging runnable

- Update the RPM host dependencies and run a native RPM build/install check.
- Verify the desktop entry, icon, QML imports, and Qt PDF dependencies on Fedora.

### 2. Add regression tests

- Run the new suite in GitHub Actions and fix any platform-specific failures.

### 3. Correct project documentation and repository hygiene

- Review generated metadata before committing and keep it out of the source change unless intentionally regenerated.

### 4. Validate the user workflow

- Run the application manually on Fedora and Windows.
- Test scan, cancel, preview, delete, smart cleanup, and filter changes on both hosts.
- Exercise unreadable files, links, disappearing files, invalid paths, and large files.
- On Windows, extract the built versioned ZIP on a clean Windows 10/11 x64 system, verify its SHA-256 sidecar, and confirm the included README and completed license.

### 5. Prepare a first release candidate

- Resolve remaining RPM and native Windows validation failures.
- Build from a clean checkout and verify the resulting artifacts in clean runtime environments.
- Tag a release only after both native package workflows pass.
