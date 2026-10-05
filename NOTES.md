# Duplicate Cleaner — Project Notes

Last reviewed: 2026-10-04

## Current status

The application implements scanning, filtering, live progress, duplicate grouping, text/image/PDF previews, and guarded cleanup through the system Trash or Windows Recycle Bin. Source, wheel, RPM, and Windows portable build recipes are present. Native package acceptance remains incomplete.

Recent fixes:

- Duplicate-list mouse-wheel input now glides with easing and accumulates repeated steps. Touchpad scrolling preserves OS momentum when supplied and estimates a short native coast when phase or momentum events are missing; scrollbar interaction stops the glide.
- Windows directory junction detection now uses file metadata available on Python 3.11, rather than relying on the newer `Path.is_junction()` API.
- Unreadable entries now obey the scan progress throttle, preventing an immediate queued UI update for every failed file. Final counts still arrive in the completion update.

Windows packaging now requires an x64 Python 3.13 interpreter, verifies the delivered ZIP and checksum, and smoke-tests the extracted executable outside the checkout from a path containing spaces and Unicode. Development Python/QML search paths are cleared for that process. The preflight sends Python code over stdin so embedded quotes are preserved by Windows PowerShell as well as PowerShell Core.

## Validation completed in this review

- Latest full suite after phase-less touchpad support: 39 tests discovered, 33 passed and six skipped (native Windows behavior and PowerShell-only archive checks unavailable on this Linux host). Six scrolling input tests cover wheel glide/accumulation, reversal/bounds, phase-aware and phase-less touchpad coasting, and scrollbar interruption.
- Added coverage for unreadable-file progress throttling, independent hard-link/symlink handling, junction metadata, PNG decoding, PDF rendering, and archive checksum/missing-content rejection.
- Added native Windows drive/UNC URL, actual directory junction, and opt-in Recycle Bin tests. They are wired into Windows CI but have not executed here.
- Both PowerShell scripts parse with temporary PowerShell 7.6.6. Archive rejection tests execute with that runtime; this does not validate Windows PowerShell 5.1 or Windows process launch behavior.
- The source archive and wheel build. The wheel contains the full QML tree, SVG/ICO assets, and license; the source archive contains the Windows recipe and validator.
- The installed wheel starts outside the checkout with the headless startup smoke check.
- The shared PyInstaller recipe builds with the pinned dependencies in an isolated environment; its Linux frozen executable passes the startup smoke check outside the checkout with development import paths cleared. Build-time warnings concern an unused Qt labs asset-downloader plugin and the optional `xxsubtype` import; no runtime QML warnings occurred.
- RPM spec expansion, build helper shell syntax, desktop entry validation, and diff whitespace checks pass.

Validation outputs are under `/tmp/duplicate-cleaner-artifacts/`, `/tmp/duplicate-cleaner-frozen-dist/`, and `/tmp/duplicate-cleaner-*.log`. These are local validation artifacts, not Windows release assets. Generated metadata from the checks is restored afterward rather than committed.

## Remaining release checks

- Native Windows execution is unverified. No Windows host is connected. The GitHub Actions API and browser page for the configured remote returned 404 without an authenticated session; no remote run result could be inspected or dispatched.
- Run the updated Windows CI matrix and executable build. The build must pass extracted-ZIP validation, then the app needs manual scan, cancellation, image/PDF preview, cleanup, and Recycle Bin restore checks on a clean Windows 10/11 x64 machine.
- The Windows CI matrix enables `DUPLICATE_CLEANER_TEST_TRASH=1`; that integration test moves only a freshly created disposable fixture and verifies the surviving copy remains. It may leave that fixture in the Recycle Bin.
- Build and install the RPM on Fedora. The system interpreter still lacks the RPM build dependency set, including `pyproject-rpm-macros`, `python3-build`, `python3-setuptools`, and `python3-wheel`. Temporary Python build environments used for this review do not satisfy those RPM dependencies.
- ~~Fill `[YEAR]` and `[COPYRIGHT HOLDER]` in the MIT license template and finish bundled third-party license/notice review before distribution.~~ ✅ MIT license issued to `isojanis`, 2026. `THIRD_PARTY_NOTICES` written and added to `MANIFEST.in`.
- Confirm the unsigned portable Windows distribution and run native acceptance before tagging or publishing a release.

## Next actions

1. Complete manual Windows acceptance using the portable ZIP in a Windows 10/11 x64 VM (see `windows-vm-testing.md`), including restoring a disposable file from the Recycle Bin.
2. Install the Fedora build prerequisites and validate the resulting RPM installation.
