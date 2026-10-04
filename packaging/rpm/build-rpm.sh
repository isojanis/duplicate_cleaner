#!/bin/sh
set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
command -v rpmbuild >/dev/null || { echo 'Install rpmbuild and the BuildRequires from duplicate-cleaner.spec.' >&2; exit 1; }
staging_dir=$(mktemp -d -t duplicate-cleaner-rpm.XXXXXXXX)
trap 'rm -rf "$staging_dir"' EXIT INT TERM

# Build from the declared source manifest, excluding environments and old outputs.
python3 -m build --sdist --outdir "$staging_dir" "$project_root"
for archive in "$staging_dir"/*.tar.gz; do
    rpmbuild -ta "$archive"
done
