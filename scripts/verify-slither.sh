#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p reports
# Reserve a new directory before invoking tools. Never delete/truncate an earlier
# successful, failed or interrupted campaign just to obtain a fresh JSON file.
if [[ -n "${POPL_SLITHER_OUTPUT_DIR:-}" ]]; then
  evidence_dir="$POPL_SLITHER_OUTPUT_DIR"
  mkdir -- "$evidence_dir"
else
  evidence_dir="$(mktemp -d reports/slither.XXXXXXXX)"
fi
trap 'printf "Static-analysis evidence: %s\n" "$evidence_dir" >&2' EXIT
slither --version > "$evidence_dir/slither-version.txt"
test "$(cat "$evidence_dir/slither-version.txt")" = '0.11.6'
set +e
slither . --config-file slither.config.json --json "$evidence_dir/slither-current.json" --disable-color \
  2>&1 | tee "$evidence_dir/slither-current.log"
pipeline_status=("${PIPESTATUS[@]}")
analyzer_status=${pipeline_status[0]}
set -e
if [[ "${pipeline_status[1]}" != 0 ]]; then
  echo "Failed to capture complete analyzer diagnostics" >&2
  exit 1
fi
# Slither returns 255 when it finds issues; success/error and full coverage are
# checked below. Other failures are not interpreted as reviewed findings.
if [[ "$analyzer_status" != 0 && "$analyzer_status" != 255 ]]; then
  echo "Slither execution failed: $analyzer_status" >&2
  exit 1
fi
python3 scripts/check-slither-review.py "$evidence_dir/slither-current.json" \
  | tee "$evidence_dir/review-coverage.json"
