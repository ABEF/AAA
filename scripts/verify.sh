#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Local untracked adapters must not hide a broken published checkout. This
# parses exact HEAD blobs without importing/executing application code.
python3 scripts/check-python-publication.py
command -v forge >/dev/null || { echo "BLOCKED: Foundry forge is not installed" >&2; exit 1; }
test -d node_modules/@openzeppelin/contracts || { echo "Install dependencies first" >&2; exit 1; }
test -d lib/forge-std || { echo "Install forge-std first" >&2; exit 1; }
# Validate actual settings before expensive work; do not print the full Forge
# configuration, which may contain private endpoints and API keys.
profile_review="$(python3 scripts/verify-normal-profile.py)"
mkdir -p reports
if [[ -n "${POPL_VERIFICATION_OUTPUT_DIR:-}" ]]; then
  evidence_dir="$POPL_VERIFICATION_OUTPUT_DIR"
  mkdir -- "$evidence_dir"
else
  evidence_dir="$(mktemp -d reports/verification.XXXXXXXX)"
fi
printf '%s\n' "$profile_review" > "$evidence_dir/toolchain-before.json"
python3 scripts/sync-project-todo.py --check
python3 scripts/generate-function-reference.py --check
python3 scripts/run_python_tests.py --output "$evidence_dir/python-tests.json"
python3 scripts/source_checks.py --output "$evidence_dir/source-checks.json"
# Python checks can inspect files; require the same effective tool/profile at
# the next boundary rather than assuming the initial observation is still valid.
profile_current="$(python3 scripts/verify-normal-profile.py)"
[[ "$profile_current" == "$profile_review" ]] || { echo "BLOCKED: verification profile changed" >&2; exit 1; }
forge --version > "$evidence_dir/foundry-version.txt"
forge build --sizes 2>&1 | tee "$evidence_dir/forge-build.log"
profile_current="$(python3 scripts/verify-normal-profile.py)"
[[ "$profile_current" == "$profile_review" ]] || { echo "BLOCKED: verification profile changed" >&2; exit 1; }
forge test -vvv 2>&1 | tee "$evidence_dir/forge-tests.log"
profile_current="$(python3 scripts/verify-normal-profile.py)"
[[ "$profile_current" == "$profile_review" ]] || { echo "BLOCKED: verification profile changed" >&2; exit 1; }
printf '%s\n' "$profile_current" > "$evidence_dir/toolchain-after.json"
printf 'Verification evidence: %s\n' "$evidence_dir"
printf '%s\n' "Local checks complete. This is NOT an audit or mainnet approval. See docs/RELEASE_CHECKLIST.md."
