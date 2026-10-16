# Migration budget and preparation static review - 2026-10-17

Fresh Slither 0.11.6 analysis completed against the final normal-profile compiler
AST/input/output and bytecode-matched artifacts from
[production attempt 3](../production/attempt3/). All 30 production Solidity
sources and three compiler/dependency configuration files remained unchanged
during analysis. Slither reused that complete build and did not invoke another
compiler. This is an internal source-delta review, not an independent audit.

| Result | Count |
| --- | ---: |
| Current detector entries | 229 |
| False positives | 138 |
| Accepted risks | 46 |
| Informational | 45 |
| Unresolved detector entries | 0 |
| Individually reviewed new or changed entries | 16 |
| Prior semantics retained after source-delta review | 213 |
| Prior entries explicitly superseded | 8 |

The 213 retained entries comprise 154 exact fingerprints and 59 changes only to
source line ranges. Their existing rationales were checked against the changed
shared authorization and valuation calls. This reuse is explicit: it is not a
fresh comprehensive audit or rerun of their historical dynamic tests. The
[triage delta](triage-delta.json) records every match, superseded entry and new
individual rationale. The prior canonical review is preserved byte for byte in
[the archive](../../history/slither-review-pre-migration-safety.json), with an
additional local [copy](prior-slither-review.json).

The five new High alerts concern historical compound amounts around `_join`
calls. Review found those values intentionally track incumbent attribution;
later compound is added to the incumbent baseline, final NAV is recomputed,
pending external receipts reject issuance, and the enclosing Vault lock remains
in force. The fixed Rewards checkpoint only performs internal accounting and
static Vault reads. The extracted immutable helper valuation is also a static
call. A second collaborating agent reviewed all five alerts separately and
agreed with the false-positive dispositions; this is still internal review.

The other eleven new or changed entries cover nine custody reentrancy reports,
the helper's initialized `Snapshot` struct, and an intentionally unused return
from the reverting exit-price guard. Each has its own source-specific rationale
and evidence in [the current review](slither-review.json). No unknown finding was
approved through similarity alone.

The 46 accepted risks remain distinct from false positives and from unresolved
detector entries. Admitted token, venue and Oracle truth; remote backing and
finality; dependency liveness; execution cost; and other recorded operating
assumptions remain qualification work. The local budget does not establish an
asynchronous bridge guarantee, recovery after chain halt, or whole-protocol
freeze/export/import. Preparation is a cancellable notice and protocol-module
configuration/new-work barrier, with permitted claims, transfers and drain
paths; inherited timelock role administration remains available.

The local helper snapshots principal and attributed idle before mutable
callbacks, adds only exact designated compound, and values the final LP plus
attributed idle with that same price vector. It requires rounded-up 97%
retention, nonzero deployed LP and at most 5% idle. Thus the guarantee is 97%
total retained value, potentially 92.15% deployed, with gas separate. Existing
ordered-pair rejects and activation/top-up 99% marginal deployment remain.
The earlier parking close, ordinary rebalance, asynchronous transport,
different-pair conversions and canonical transitions are outside this budget.

The official coverage CLI passed with no errors; its result is recorded in
[coverage-check.json](coverage-check.json). The unchanged 43 matcher cases were
executed once in this workstream before the instruction to reuse them, and that
actual pass is preserved without another run. Nine fresh mutations of the new
helper finding/review/source binding all rejected: changed expression, severity,
confidence, missing/duplicate/new finding, unresolved disposition, missing
rationale and source drift. See [mutation checks](mutation-tests.json),
[matcher execution](matcher-tests.json) and [coverage](coverage.json).

The first preflight rejected incomplete incremental compiler AST evidence before
Slither analysis. A fresh normal build repaired that evidence without a Solidity
change. Its [failed preflight](failed-preflight.json) is preserved separately
from the successful [run summary](run-summary.json). The summary binds the raw
analyzer output, complete compiler input/AST and tool hashes at their external
workspace paths. Existing historical analyzer outputs were not overwritten.

This review does not assert fresh fork or production gas qualification. The
normal runtime limits currently have only 17 bytes free in Vault and 30 in
Migration. Current dynamic checks are reported separately in the parent
[verification record](../VERIFICATION.md); production services, authorities,
routes, operating qualification and independent audit remain open.
