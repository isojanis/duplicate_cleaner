# Duplicate Cleaner test plan

## Automated checks

From a clean Python 3.11+ environment, install `.[test,dev]`, set `QT_QPA_PLATFORM=offscreen` and `QT_QUICK_BACKEND=software` on headless Linux, then run:

```sh
python -m unittest discover -s tests -v
python -m duplicate_cleaner --smoke-test
python -m build
```

CI runs these checks on Linux and Windows with Python 3.11 and 3.13. It also installs the built wheel outside the checkout and starts that installed application. The Windows artifact job builds a portable ZIP, checks its SHA-256 sidecar and required files, and launches the extracted executable from a path containing spaces and Unicode.

The 2026-10-21 local run passed 45 tests with seven platform-specific skips (52 discovered), and the QML startup smoke check passed. Three consecutive full-suite runs passed. Branch-aware coverage measured 80% of Python code; this excludes QML and does not count the separate startup smoke process.

| Area | Automated coverage | Remaining acceptance work |
| --- | --- | --- |
| Duplicate detection | Size and SHA-256 grouping, hard links, symlinks, junction tag, filters, limits, cancellation, unreadable files, progress, changing files | Large trees and network/removable drives on target systems |
| Cleanup safety | Changed target/survivor, final copy, unknown path, cancellation, Trash failure, opened-file identity after replacement, mixed batch continuing after a changed file | Native Linux Trash and Windows Recycle Bin restore, concurrent file replacement during OS move |
| Interface | Offscreen QML load and Start scan action, scroll behavior, filter settings across restart, scan cancellation/failure, stale-result clearing, preview, status, worker shutdown | Keyboard, screen reader, scaling, dark/light themes on real desktops |
| Packages | Wheel startup, Windows ZIP checksum/content/startup rejection cases | Install and launch RPM on supported Fedora versions; native Windows release acceptance |
| Licenses | Project MIT license and notice index included in package recipes | Collect and review complete platform-specific runtime license/copyright texts before public binary release |

The remaining automated gaps are mainly startup path selection and failure handling, dialogs and keyboard actions in QML, and native platform behavior. The startup smoke check covers the normal startup path outside the coverage run. Coverage is a guide to missing paths, not proof that file deletion is safe.

## Manual release checks

Use disposable copies of files. On each target platform, scan folders with nested duplicates, inspect text/image/PDF previews, stop a scan, try each filter, move one duplicate to Trash or Recycle Bin, restore it, and confirm the retained copy is unchanged. Repeat with a modified file after scanning and with a symlink or junction. Check that installed package assets load without a source checkout. Record the OS, package version, Qt/PySide version, result, and any skipped step in the release notes.

A scan is a snapshot. The application revalidates content before cleanup, but the path-based Qt Trash operation cannot make validation and moving atomic. The test suite cannot prove safety against an adversary swapping a path at that final instant. Do not claim that race is closed without a different platform-specific move design.
