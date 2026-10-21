# License audit and distribution status

Reviewed 2026-10-21 against the repository and the pinned Windows build recipe.
This is an engineering audit, not a certification of legal compliance.

## Project source and dependency packaging

The project has an MIT license with an identified copyright holder. Python and
QML sources and the geometric SVG/ICO project icons are covered by that grant.
No external icon pack, font, or copied third-party source was identified in the
application tree. This review cannot independently prove authorship of every
past contribution.

The wheel and source distribution carry the project license, dependency notice
index, this audit, and the upstream license texts under `LICENSES/`. They do not
vendor the Python interpreter or Qt. RPMs use distro dependencies. The MIT
package metadata describes the project code, not the separately licensed Qt
runtime. Package-content tests check exact notice contents, not just filenames.

## Frozen Windows builds: not cleared for public release

A passing startup test or a present LICENSE file does not establish that all
bundled dependency obligations have been met. The prior notice index incorrectly
claimed that no GPL-only Qt modules were used, without inspecting the frozen
payload. It also omitted Qt PDF/SVG and described PyInstaller as build-only.
Those statements have been corrected.

The recipe now produces explicitly unreviewed test archives, includes the
upstream LGPL/GPL and PyInstaller texts, and copies the build interpreter's
Python license. CI builds and smoke-tests them but does not upload the binary
as a downloadable release artifact. To enable public binary distribution:

1. Inventory the exact PyInstaller output: Python packages, Qt libraries and QML
   plugins, image codecs, PDFium/Chromium components, fonts, runtime hooks, and
   Microsoft runtime DLLs. Record versions, source locations, and hashes.
2. Match every shipped component to its license and copyright/NOTICE texts,
   using the exact source revision or upstream SBOM. Include all required texts.
   Qt's LGPL text alone does not cover its third-party components.
3. Establish and verify the applicable corresponding-source delivery mechanism
   for the exact LGPL binaries, including patches and build information. Generic
   upstream home-page links are not evidence that this has been satisfied.
4. Test replacement of the shipped LGPL shared libraries with compatible builds;
   retain instructions and the test result with the release record.
5. Inspect the final archive and record the audit against its SHA-256. A later
   change to dependencies or bundled files requires a fresh artifact review.

The old EXE and source tarball were removed from the current repository tree
because they predate these checks. Local backup copies were retained during the
cleanup. Git history was not rewritten; any historical downloads or external
releases still need separate review or withdrawal.

## Upstream references checked

- [Qt 6.11.2 third-party components](https://doc.qt.io/qt-6.11/licenses-used-in-qt.html)
- [Qt PDF licensing](https://doc.qt.io/qt-6.11/qtpdf-index.html)
- [Qt SVG licensing](https://doc.qt.io/qt-6.11/qtsvg-index.html)
- [Qt LGPL obligations](https://www.qt.io/development/open-source-lgpl-obligations)
- [PyInstaller licensing](https://pyinstaller.org/en/stable/license.html)
- Exact license-text origins and hashes: [LICENSES/README.md](LICENSES/README.md)
