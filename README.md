# Duplicate Cleaner

A Qt Quick desktop app for finding identical files on Linux and Windows. Files are grouped by size and SHA-256 content hash. The interface uses standard Qt controls and the desktop palette; KDE/Kirigami is not required.

Features include recursive scanning, progress and cancellation, size/extension/folder filters, persistent preferences, text/image/PDF previews, sorting, and smart cleanup of same-folder duplicates with similar names.

## Cleanup behavior

Removal moves files to the system Trash or Windows Recycle Bin. There is no permanent-delete fallback. Restore files using your file manager. Cleanup checks scan fingerprints and rehashes the target and a surviving copy before moving a file; changed files, unknown paths, links, and last copies are refused. Smart cleanup retains the oldest **modification time**, not necessarily the original creation time.

Scan results describe a point in time. Avoid concurrently editing the files being cleaned: filesystem changes can still occur between validation and the OS move operation. Hard links are counted once rather than presented as reclaimable copies. Folder symlinks/junctions are not followed. A default 1 GB maximum file size and 1,000-candidate hashing limit bound scans; adjust these in Scan filters for larger searches. Stopped and limited scans are partial results.

## Linux: host Qt setup

Use Python 3.11+ and matching distro packages for PySide6, Qt Quick Controls, Qt PDF, and Qt SVG (Qt 6.8+). Keep all Qt libraries from the same source.

```sh
python3 -m venv --system-site-packages .venv
. .venv/bin/activate
python -m pip install -e '.[dev]' --no-deps
python -m duplicate_cleaner
```

The editable install provides the `duplicate-cleaner` entry point as well; `PYTHONPATH=src` is only needed when running directly from an uninstalled checkout. The application defaults Qt Quick Controls to Fusion, so a shell style override is not normally needed.

The existing VS Code host tasks remain available. For an isolated pip-based Qt environment instead, create a fresh environment **without** system site packages and install `.[portable,dev]`. Do not inject host QML/plugin paths into a pip Qt runtime.

## Windows: run from source

Use 64-bit Python 3.11+ on Windows 10/11. PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install -e .
.\.venv\Scripts\python -m duplicate_cleaner
```

Windows dependencies install PySide6 automatically. Folder opening uses the OS default file manager. Local file URLs support spaces, Unicode, drive letters, and UNC paths. Ctrl+O opens the folder picker; Escape cancels a scan. Tab through result rows and press Enter to preview or Delete to open the removal confirmation.

## Windows: portable executable

Build **on Windows** using 64-bit Python 3.13 and a dedicated environment. The pinned build dependencies are in `packaging/windows/requirements-build.txt`:

```powershell
py -3.13 -m venv .venv-build
.\.venv-build\Scripts\Activate.ps1
python -m pip install -r packaging/windows/requirements-build.txt
.\packaging\windows\build.ps1
```

The script builds a folder-based executable, runs its startup smoke check, and writes `dist/DuplicateCleaner-<version>-windows-x64.zip` with a `.sha256` sidecar. The bundle includes the project README and license. Extract the **whole folder** and launch `DuplicateCleaner.exe`; Python and KDE are not needed on the destination machine. This is a portable distribution, not an installer. Builds are unsigned. Fill in the license template and review bundled third-party license notices before distribution, including the applicable [Qt for Python license terms](https://doc.qt.io/qtforpython-6/commercial/index.html). Native Windows acceptance testing is required before release.

## Tests and packages

With Qt installed:

```sh
python -m unittest discover -s tests -v
python -m duplicate_cleaner --smoke-test
python -m pip install build
python -m build
```

On headless Linux use `QT_QPA_PLATFORM=offscreen` and, when needed, `QT_QUICK_BACKEND=software`. The smoke check opens the complete QML interface using temporary settings and exits with a failure status if it cannot load or emits QML warnings. Unit tests use temporary files/settings and mock Trash operations; they do not remove your files.

Both wheels and source archives include the interface and icon. On a Fedora RPM build host with the spec's BuildRequires installed, run `sh packaging/rpm/build-rpm.sh`. The script builds a source archive from the manifest, avoiding virtual environments and existing build output, then places RPMs under `dist/rpm/RPMS/`. RPM installs package-local UI assets along with the desktop entry, icon, and license file. The RPM spec is Fedora-style and still needs validation on a native RPM host. `LICENSE` is an MIT template with placeholder copyright fields; fill those in before public distribution.

GitHub Actions defines Linux/Windows tests, installed-wheel startup checks, and a Windows executable artifact build. These workflows must pass on the remote runners; adding the workflow does not mean it has already run. The Windows artifact job produces a versioned ZIP and SHA-256 sidecar; it does not publish a GitHub Release.

See [PLAN.md](PLAN.md) for milestones and [NOTES.md](NOTES.md) for verified status and remaining release checks.

Packaging references: [Qt deployment](https://doc.qt.io/qtforpython-6/deployment/deployment-pyinstaller.html), [PyInstaller hooks](https://pyinstaller.org/en/stable/hooks.html), and [Qt Trash support](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QFile.html).
