# Duplicate Cleaner

A Qt Quick desktop app for finding identical files on Linux and Windows. Files are grouped by size and SHA-256 content hash. The interface uses standard Qt controls and the desktop palette; KDE/Kirigami is not required.

Features include recursive scanning, progress and cancellation, size/extension/folder filters, persistent preferences, text/image/PDF previews, sorting, and smart cleanup of same-folder duplicates with similar names.

## License and release status

Project code is [MIT licensed](LICENSE). Dependencies retain their own terms;
see [third-party notices](THIRD_PARTY_NOTICES) and [upstream license texts](LICENSES/README.md).
The application is currently an alpha. Source and wheel builds do not bundle Qt.
Windows executable builds are **unreviewed engineering test builds**, pending the
specific dependency and source-delivery checks in [LICENSE_AUDIT.md](LICENSE_AUDIT.md).
Use the source setup below to run the application.


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

## Windows: engineering test build

Build **on Windows** using 64-bit Python 3.13 and a dedicated environment. The pinned build dependencies are in `packaging/windows/requirements-build.txt`:

```powershell
py -3.13 -m venv .venv-build
.\.venv-build\Scripts\Activate.ps1
python -m pip install -r packaging/windows/requirements-build.txt
.\packaging\windows\build.ps1
```

The script requires an x64 Python 3.13 interpreter and writes `dist/DuplicateCleaner-<version>-windows-x64-unreviewed.zip` with a `.sha256` sidecar. It verifies the checksum and required files, extracts to a temporary path with spaces and Unicode outside the checkout, and runs the extracted executable's startup smoke check with development Python/QML paths cleared. To select Python without activating the environment, pass `-Python .\.venv-build\Scripts\python.exe` to `build.ps1`.

The test bundle includes the project README, MIT license, notice index, audit status, upstream LGPL/GPL and PyInstaller texts, and the build interpreter's Python license. Extract the **whole folder** and launch `DuplicateCleaner.exe`; Python and KDE are not needed on the destination machine. This is a portable distribution, not an installer. Builds are unsigned. The remaining binary audit is described in [LICENSE_AUDIT.md](LICENSE_AUDIT.md). Native Windows acceptance testing is required before release.

To validate an existing archive on Windows, keep its `.sha256` file beside it and run:

```powershell
.\packaging\windows\validate-portable.ps1 -Archive .\dist\DuplicateCleaner-0.1.0-windows-x64-unreviewed.zip
```

## Tests and packages

In an isolated virtual environment, install the test extras:

```sh
python -m pip install -e ".[test,dev]"
python -m unittest discover -s tests -v
python -m duplicate_cleaner --smoke-test
python -m pip install build
python -m build
python packaging/check_distributions.py dist
```

On headless Linux use `QT_QPA_PLATFORM=offscreen` and, when needed, `QT_QUICK_BACKEND=software`. The smoke check opens the complete QML interface using temporary settings and exits with a failure status if it cannot load or emits QML warnings. Tests use temporary files/settings. Archive rejection tests require PowerShell (`pwsh` or `powershell`); native Windows path and junction tests skip on other systems.

Trash operations are mocked by default. The Windows CI matrix explicitly sets `DUPLICATE_CLEANER_TEST_TRASH=1` to enable the Recycle Bin integration test: it moves one newly created, disposable test file to the Recycle Bin and verifies the surviving copy is retained. Set that environment variable when running native acceptance tests locally as well. The generated test file can remain in the Recycle Bin afterward.

Both wheels and source archives include the interface and icon. On a Fedora RPM build host with the spec's BuildRequires installed, run `sh packaging/rpm/build-rpm.sh`. The script builds a source archive from the manifest, avoiding virtual environments and existing build output, then places RPMs under `dist/rpm/RPMS/`. RPM installs package-local UI assets along with the desktop entry, icon, and license file. The RPM spec is Fedora-style and still needs validation on a native RPM host. `LICENSE` contains the project MIT grant and copyright notice. The wheel and RPM carry the notice index, audit status, and upstream license texts. A frozen runtime requires the separate binary audit.

GitHub Actions defines Linux/Windows tests, installed-wheel startup checks, and a Windows executable artifact build. These workflows must pass on the remote runners; adding the workflow does not mean it has already run. The Windows job builds and smoke-tests an unreviewed ZIP and SHA-256 sidecar. It does not upload binaries or publish a GitHub Release while the binary license audit is incomplete.

See [TEST_PLAN.md](TEST_PLAN.md) for coverage and manual checks, [SECURITY.md](SECURITY.md) for the security policy, and [NOTES.md](NOTES.md) for verified status and remaining release checks.

Packaging references: [Qt deployment](https://doc.qt.io/qtforpython-6/deployment/deployment-pyinstaller.html), [PyInstaller hooks](https://pyinstaller.org/en/stable/hooks.html), and [Qt Trash support](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QFile.html).
