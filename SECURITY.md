# Security policy

## Supported versions

Security fixes target the latest `0.1.x` release and the current main branch. Older builds may not receive fixes.

## Reporting

Please report suspected vulnerabilities privately to the repository maintainer through GitHub private vulnerability reporting when available. If that feature is unavailable, contact the maintainer privately before opening a public issue. Include the version, operating system, reproduction steps, and whether the issue can cause file loss or expose local files. Do not include sensitive file contents in the report.

## File safety and limitations

Duplicate Cleaner reads files under the selected folder, stores scan preferences through Qt settings, and moves selected duplicates to the operating system Trash or Recycle Bin. It does not offer permanent deletion or upload files. The cleaner checks that the selected file and at least one survivor still match the scan and refuses links, changed files, and the final copy.

The final Qt Trash call uses a path. A separate process can change that path after validation and before the move. Avoid cleaning folders that other processes are modifying concurrently. The open-file identity checks reduce scan and verification races, but they do not make the final move atomic.
