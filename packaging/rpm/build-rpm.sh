#!/bin/sh
set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
command -v rpmbuild >/dev/null || { echo 'Install rpmbuild and the BuildRequires from duplicate-cleaner.spec.' >&2; exit 1; }
staging_dir=$(mktemp -d -t duplicate-cleaner-rpm.XXXXXXXX)
trap 'rm -rf "$staging_dir"' EXIT INT TERM
(cd "$staging_dir" && python3 -m build --version >/dev/null 2>&1) || {
    echo 'Install the Python build package (python3-build on Fedora).' >&2
    exit 1
}
rpm_topdir="$project_root/dist/rpm"
mkdir -p "$rpm_topdir/BUILD" "$rpm_topdir/BUILDROOT" "$rpm_topdir/RPMS" \
    "$rpm_topdir/SOURCES" "$rpm_topdir/SPECS" "$rpm_topdir/SRPMS"

# Build from the declared source manifest, excluding environments and old outputs.
(cd "$staging_dir" && python3 -m build --sdist --outdir "$staging_dir" "$project_root")
for archive in "$staging_dir"/*.tar.gz; do
    rpmbuild --define "_topdir $rpm_topdir" -ta "$archive"
done
