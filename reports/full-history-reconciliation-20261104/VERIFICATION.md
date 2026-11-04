# Verification and evidence boundaries

Baseline `a915b6a12e42dac0685ff9cad5f0fa17bfd78e23`.
This is report/obligation reconciliation plus a static-review entrypoint repair,
not another full contract/security audit. See [review](REVIEW.md),
[inventory](HISTORY_INVENTORY.json), [finding provenance](FINDINGS.json).

## New verification

The previous default checker was applied to the captured manual-safeguard
detector output: it rejected four differences (two changed source bindings and
the affected detector identities). That negative result is preserved externally
as STATIC_BEFORE.json. The new full [review](static-review.json) passes the
**unchanged strict matching rules** against that same captured output.

44distinct selected `SlitherReviewTests` pass, with no failures/errors/skips.
One new regression loads the actual default, verifies its current source/toolchain
inventory and reconstructible finding descriptions/rationales. Existing negative
cases cover source drift, unexpected/missing/duplicate/unresolved findings,
changed expressions/locations/call trees, severity, multiplicity and narrowly
allowed nondeterministic presentation. No external raw analyzer file is needed
for the new published test; actual captured-output matching is a separate check.

471detector records retain13changed-source context rationales and458exact
referenced-context dispositions from the prior manual-safeguard review. A
one-to-one exact check/severity/confidence/description-line-multiset mapping
reconstructs the full record; only the13already-reviewed changed contexts omit
line numbers for that historical mapping. The runtime checker does NOT use that
mapping rule: it continues its existing strict source/fingerprint/tree/bundle
rules. No findings are silently removed, deduplicated or accepted without rationale.

No analyzer, compiler, Foundry suite, RPC/fork, browser, service or on-chain
operation was newly executed. Exact unchanged52production/31dependency/4build
pins permit reuse of the manual-safeguard43normal gates and original selected
EVM evidence. Counts from earlier overlapping campaigns are not added. Runtime
headroom remains Migration39/Vault635/Budget237/Balancer360bytes.

## Reconciliation verification

All310original matrix JSON pointers and canonical record hashes are checked.
Original235historical/75later rows, prior subsequent findings and post-matrix
reviews remain separate.398pre-ledger unchecked lines retain full text; all
five removed structured task IDs have explicit removal/architecture disposition.
The22current topics bind current references/owning task IDs;16material original
rows have specific updated dispositions rather than a blanket topic closure.

The input manifest and catalogue preserve current narrative hashes, main-history
blob witnesses, deleted paths, website history and local-only draft hashes.
Automated full-text/extraction coverage does not certify every paragraph as an
independently adjudicated vulnerability. Historical tests and advisories remain
source/date scoped; no green published CI or independent approval is asserted.

Final preservation, exact maintained-doc links, generated sole Todo, staged and
committed Python publication closure are recorded in the campaign's final
evidence manifest. Four unrelated tracked dirty files and all original report
inputs except mutable reports/README.md must remain byte-identical. The website
checkout is read-only and all existing service/site/Anvil/journal/signer/heartbeat
boundaries remain unchanged.

Raw extraction, original dirty-doc backups, source snapshots, negative control,
exact original-pointer data and selected test logs are retained in the external
full-history-reconciliation-20261104 evidence directory. Public structured
records include their hashes without credentials or private transport material.
