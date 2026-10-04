# Linux and Windows delivery plan

## Objective

Deliver a polished Linux duplicate cleaner and a Windows version sharing the scanner and application logic. Preserve the host Qt/Kirigami development setup on Linux. Treat native runtime checks as release requirements, not as implied successes from source inspection.

## Milestones

### 1. Reliable packaging

- [x] Ship all QML components and the application icon in distributable artifacts.
- [x] Resolve assets from an installed package, source checkout, and frozen executable.
- [ ] Fix RPM installation and file ownership declarations.
- [x] Verify wheel and source archive contents and launch from an installed layout.

### 2. Linux workflow and safeguards

- [x] Review cancellation and application exit while scanning.
- [x] Make deletion behavior explicit and preserve a surviving duplicate.
- [x] Review stale scan results, symlinks, and files changed since scanning.
- [x] Keep previews responsive and bound text preview reads.
- [x] Verify empty states, errors, progress, keyboard use, and small-window layout.

### 3. Regression coverage

- [x] Test scanner grouping, filters, limits, cancellation, and filesystem edge cases.
- [x] Test cleanup selection and deletion safeguards with temporary fixtures.
- [x] Test asset resolution and platform-specific integration.
- [x] Add continuous integration for Linux and Windows.

### 4. Windows delivery

- [x] Choose a portable Qt interface strategy that does not require Windows users to install KDE.
- [x] Support Windows paths, file URLs, and opening files in Explorer.
- [x] Declare Windows runtime dependencies separately from Linux host packages.
- [x] Pin the Windows executable build dependencies in a separate requirements file.
- [x] Provide a reproducible Windows executable build and installation instructions.
- [x] Include the app icon, project license, and README in the portable bundle; emit a versioned ZIP and checksum.
- [ ] Validate the packaged app on native Windows, including scanning, previews, cancellation, and deletion.
- [ ] Complete license and bundled third-party notice review before distribution.

### 5. Documentation and release checks

- [x] Replace stale scaffold documentation with supported workflows and limitations.
- [x] Document development, tests, Linux packaging, and Windows builds.
- [x] Ignore generated artifacts while preserving existing user changes.
- [x] Record local verification results and checks requiring another host in NOTES.md.
- [ ] Complete native Linux and Windows acceptance checks before declaring release readiness.
- [ ] Verify the Windows ZIP and checksum from a clean Windows 10/11 x64 environment.

## Completion policy

Mark an item complete only after implementation and relevant verification. Building an artifact is distinct from validating its native user workflow. Record unavailable tooling or platforms explicitly. Do not publish or tag releases as part of this implementation without a separate request.
