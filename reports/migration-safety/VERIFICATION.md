# Migration safety verification

Development evidence, 2026-10-17. **Not production approval or an independent
audit.** No public transactions, production deployment or server upgrade.

## Frozen contract source

[Focused tests](focused/attempt1/receipt.json): **28 passed**, zero failures or
skips: ten canonical-preparation integration cases, five migration execution/
valuation cases and thirteen migration adversarial cases. The receipts bind
compiler artifacts, tool hashes and exact before/after source hashes. Local
venue, price, randomness and transport fixtures remain explicit limitations.

[The final normal production build](production/attempt3/receipt.json) passes all
**24 runtime/initcode-object size gates** with bindings for **30 production
sources**. [The size manifest](production/attempt3/size-gates.json) records exact
objects and compiler settings. Vault is 24,559 runtime bytes; Migration is 24,546.
Constructor arguments and actual target-chain gas still require qualification.

The [remaining affected offline suites](regression/attempt1/receipt.json) passed
**551 tests**, with zero failures and two intentional opt-in fork setup skips.
Combined with the disjoint 28-case focused run, this is **579 passes / zero
failures / two expected skips**, 581 cases across 49 suites. The
[combined inventory](verification-summary.json) verifies that the runs have no
overlapping cases and that all recorded source/configuration hashes still match.
The large regression output is stored as a lossless gzip archive; its storage
manifest binds the compressed and original bytes to the execution receipt.

## Fresh static analysis

[The new Slither run and internal review](static-analysis/README.md) cover all 30
production sources and three build/configuration files: **229 detector entries**,
classified as **138 false positives / 46 accepted risks / 45 informational / zero
unresolved detector entries**. Accepted risks remain risks; this is not an audit
approval. Sixteen new/changed entries were individually reviewed; 213 retained
prior dispositions have documented semantic matches, and eight old entries are
explicitly superseded. Coverage passes; nine new-helper review/source mutations
are rejected. The actual one-time 43 matcher-test pass is preserved separately.
No production source changed during analysis. The prior canonical review and
failed incomplete-AST preflight are preserved byte-for-byte/separately as stated
in the report.

## Python and configuration scope

The [preparation-aware keeper receipt](../canonical-preparation/keeper/verification.json)
records **185 passes**, zero failures/errors/runtime skips, with one explicit
POSIX-only exclusion from its 186-case inventory. No new real-process server
rehearsal is claimed. Existing staging was not updated.

The production manifest suite ran **126 tests successfully** before the later
mixed-case alias correction (`python -m unittest discover -s tests_python -p
test_production_config.py`; console result: 126 tests in 19.589s, OK). That run
was console-only and is not claimed as a final-source complete-suite receipt.
After review identified the alias issue, only the new case and three directly
affected alias cases were rerun: **4 passes**, zero failures/errors/skips, with
[source-bound evidence](config-review/verification.json). Unchanged unrelated
tests were not repeated for a larger count.

The narrow source-consistency checker reports 30 source files and no errors;
it does not replace compilation or security analysis.

## Earlier attempts and evidence boundaries

- [Production attempt 1](production/attempt1/receipt.json) failed the standard
  Migration runtime-size gate (24,835 bytes). Identical-semantics check factoring
  corrected it; no size limit was increased.
- [Production attempt 2](production/attempt2/receipt.json) passed build and object
  gates. Static-analysis preflight then rejected its incremental build-info for
  an incomplete dependency AST. Attempt 3 compiled into a fresh output/cache to
  provide a complete typed compilation unit; tests were not repeated for that
  compiler-evidence repair.
- Earlier preparation development included a test-only prank/getter-ordering
  correction. Final focused execution uses the frozen corrected tests. Earlier
  agent runs are not added to the final 28-test count.
- [Keeper earlier attempts](../canonical-preparation/keeper/prior-attempts.json)
  remain separately documented; unavailable raw logs are not reconstructed.

No fresh live-RPC fork, extended audit invariant profile, Robinhood Testnet run,
external proof qualification or independent audit was performed in this scope.
Older fork/staging reports retain their original source and service identities.
