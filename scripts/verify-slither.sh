#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
test "$(slither --version)" = '0.11.6'
mkdir -p reports/production
# A new report is required for each invocation; a stale successful JSON cannot pass.
rm -f reports/production/slither-current.json
set +e
slither . --config-file slither.config.json --json reports/production/slither-current.json --disable-color \
  2>&1 | tee reports/production/slither-current.log
analyzer_status=${PIPESTATUS[0]}
set -e
# Slither returns 255 when it finds issues; success/error and full coverage are
# checked below. Other failures are not interpreted as reviewed findings.
if [[ "$analyzer_status" != 0 && "$analyzer_status" != 255 ]]; then
  echo "Slither execution failed: $analyzer_status" >&2
  exit 1
fi
python3 scripts/check-slither-review.py reports/production/slither-current.json
