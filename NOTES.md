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
- Qt Quick/Kirigami interface with scan, results, preview, filter, and cleanup panels.
- Basic RPM packaging metadata and desktop integration.

## Verification completed

- `python3 -m compileall -q src/duplicate_cleaner` passes.
- A temporary-folder smoke test successfully found three identical files in one duplicate group.
- The Python wheel contains the current Python package, including `scanner.py`.

## Known gaps

- There is no automated test suite.
- `README.md` still describes scanning and deletion as placeholders; that is no longer accurate.
- The wheel does not include the QML interface.
- The RPM spec installs `qml/Main.qml` but not `qml/components/*.qml`, even though `Main.qml` imports that directory.
- The application has not yet been validated end-to-end from an installed RPM or a clean environment with the host Qt/Kirigami stack.
- Generated packaging/build output is currently present as untracked worktree content (`build/`, `dist/`, and generated `egg-info` changes). Decide whether these belong in version control or should be ignored.

## Next-step plan

### 1. Make packaging runnable

- Update the RPM spec to install the complete `qml/` tree, including all component files.
- Decide on the distribution strategy for QML: package it as RPM data files, include it in the Python distribution, or both.
- Rebuild the wheel/RPM and test launching from the installed layout.
- Verify the desktop entry, icon, QML imports, and Qt PDF/Kirigami dependencies.

### 2. Add regression tests

- Add scanner tests for identical files, different files, empty-file handling, recursion, size filters, extension filters, folder patterns, search limits, and cancellation.
- Add bridge tests for size parsing, settings persistence, deletion behavior, preview metadata, and smart cleanup.
- Keep tests independent of a graphical display where possible.

### 3. Correct project documentation and repository hygiene

- Update `README.md` from “UI scaffold” language to the current prototype capabilities and limitations.
- Document how to run the scanner smoke tests and how to build/install packages.
- Add appropriate `.gitignore` entries for virtual environments, build output, distributions, caches, and generated metadata if those files are not intentionally tracked.
- Regenerate metadata only through the documented build workflow.

### 4. Validate the user workflow

- Run the application on the target host Qt/Kirigami environment.
- Test scan, cancel, preview, delete, smart cleanup, and filter changes manually.
- Check behavior for unreadable files, symlinks, files disappearing during a scan, invalid paths, and very large files.
- Review destructive-action messaging and confirm that deletion behavior matches the intended product policy.

### 5. Prepare a first release candidate

- Resolve packaging and test failures.
- Choose and document the supported Linux distribution(s) and dependency versions.
- Build from a clean checkout and verify the resulting artifact in a clean runtime environment.
- Tag a release only after the installed-package workflow passes.
