#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v npm >/dev/null || { echo "Install a reviewed Node/npm release first" >&2; exit 1; }
command -v git >/dev/null || { echo "git is required" >&2; exit 1; }
mkdir -p reports lib
# A missing lockfile is a reproducibility error; never silently re-resolve packages.
test -f package-lock.json || { echo "Committed package-lock.json is required" >&2; exit 1; }
# Do not execute third-party npm lifecycle scripts.
npm ci --ignore-scripts
forge_std_commit=77041d2ce690e692d6e03cc812b57d1ddaa4d505
if ! test -d lib/forge-std; then
  git clone --depth 1 --single-branch --branch v1.9.7 https://github.com/foundry-rs/forge-std.git lib/forge-std
fi
test "$(git -C lib/forge-std rev-parse HEAD)" = "$forge_std_commit" || {
  echo "forge-std must match reviewed commit $forge_std_commit" >&2; exit 1;
}
test -z "$(git -C lib/forge-std status --porcelain --untracked-files=all)" || {
  echo "forge-std checkout contains unreviewed local changes" >&2; exit 1;
}
{
  npm ls --depth=0
  printf 'forge-std commit: '
  git -C lib/forge-std rev-parse HEAD
} > reports/dependencies-resolved.txt
printf '%s\n' "Locked npm packages and the reviewed forge-std revision are installed; release review remains required."
