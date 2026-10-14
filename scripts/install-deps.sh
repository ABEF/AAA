#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v npm >/dev/null || { echo "Install a reviewed Node/npm release first" >&2; exit 1; }
command -v git >/dev/null || { echo "git is required" >&2; exit 1; }
mkdir -p reports lib
# Do not run third-party npm lifecycle scripts. No lockfile is fabricated in this archive.
if test -f package-lock.json; then npm ci --ignore-scripts; else npm install --ignore-scripts; fi
if ! test -d lib/forge-std; then
  git clone --depth 1 --single-branch --branch v1.9.7 https://github.com/foundry-rs/forge-std.git lib/forge-std
fi
test "$(git -C lib/forge-std describe --tags --exact-match HEAD)" = v1.9.7
{
  npm ls --depth=0
  printf 'forge-std commit: '
  git -C lib/forge-std rev-parse HEAD
} > reports/dependencies-resolved.txt
printf '%s\n' "Review and commit package-lock.json and immutable upstream revisions before release."
