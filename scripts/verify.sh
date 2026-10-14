#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p reports
python3 scripts/run_python_tests.py
python3 scripts/source_checks.py
command -v forge >/dev/null || { echo "BLOCKED: Foundry forge is not installed" >&2; exit 1; }
test -d node_modules/@openzeppelin/contracts || { echo "Install dependencies first" >&2; exit 1; }
test -d lib/forge-std || { echo "Install forge-std first" >&2; exit 1; }
forge --version > reports/foundry-version.txt
forge build --sizes 2>&1 | tee reports/forge-build.log
forge test -vvv 2>&1 | tee reports/forge-tests.log
printf '%s\n' "Local checks complete. This is NOT an audit or mainnet approval. See docs/RELEASE_CHECKLIST.md."
