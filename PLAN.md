# Linux and Windows delivery plan

## Objective

Deliver a polished Linux duplicate cleaner and a Windows version sharing the scanner and application logic. Preserve the host Qt/Kirigami development setup on Linux. Treat native runtime checks as release requirements, not as implied successes from source inspection.

## Milestones

### 1. Reliable packaging

- [ ] Ship all QML components and the application icon in distributable artifacts.
- [ ] Resolve assets from an installed package, source checkout, and frozen executable.
- [ ] Fix RPM installation and file ownership declarations.
- [ ] Verify wheel and source archive contents and launch from an installed layout.

### 2. Linux workflow and safeguards

- [ ] Review cancellation and application exit while scanning.
- [ ] Make deletion behavior explicit and preserve a surviving duplicate.
- [ ] Review stale scan results, symlinks, and files changed since scanning.
- [ ] Keep previews responsive and bound text preview reads.
- [ ] Verify empty states, errors, progress, keyboard use, and small-window layout.

### 3. Regression coverage

- [ ] Test scanner grouping, filters, limits, cancellation, and filesystem edge cases.
- [ ] Test cleanup selection and deletion safeguards with temporary fixtures.
- [ ] Test asset resolution and platform-specific integration.
- [ ] Add continuous integration for Linux and Windows.

### 4. Windows delivery

- [ ] Choose a portable Qt interface strategy that does not require Windows users to install KDE.
- [ ] Support Windows paths, file URLs, and opening files in Explorer.
- [ ] Declare Windows runtime dependencies separately from Linux host packages.
- [ ] Provide a reproducible Windows executable build and installation instructions.
- [ ] Validate the packaged app on native Windows, including scanning, previews, cancellation, and deletion.

### 5. Documentation and release checks

- [ ] Replace stale scaffold documentation with supported workflows and limitations.
- [ ] Document development, tests, Linux packaging, and Windows builds.
- [ ] Ignore generated artifacts while preserving existing user changes.
- [ ] Record local verification results and checks requiring another host in NOTES.md.
- [ ] Complete native Linux and Windows acceptance checks before declaring release readiness.

## Completion policy

Mark an item complete only after implementation and relevant verification. Building an artifact is distinct from validating its native user workflow. Record unavailable tooling or platforms explicitly. Do not publish or tag releases as part of this implementation without a separate request.
