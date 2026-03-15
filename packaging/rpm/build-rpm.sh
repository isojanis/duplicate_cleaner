#!/bin/sh
set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
version=$(sed -n 's/^version = "\([^"]*\)"$/\1/p' "$project_root/pyproject.toml" | head -n 1)
name=duplicate-cleaner
archive_dir="$project_root/dist"
archive_name="$name-$version"
staging_dir=$(mktemp -d)
archive_root="$staging_dir/$archive_name"
archive_path="$archive_dir/$archive_name.tar.gz"

cleanup() {
    rm -rf "$staging_dir"
}
trap cleanup EXIT INT TERM

mkdir -p "$archive_dir"
mkdir -p "$archive_root"

cp -a "$project_root/." "$archive_root/"
rm -rf "$archive_root/.git" "$archive_root/dist" "$archive_root/.venv" "$archive_root/__pycache__"
find "$archive_root" -name __pycache__ -type d -prune -exec rm -rf {} +
find "$archive_root" -name '*.pyc' -delete

tar -C "$staging_dir" -czf "$archive_path" "$archive_name"
rpmbuild -ta "$archive_path"
