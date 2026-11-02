# Verification, failures and reuse

Baseline main `9bd13dfbc5a6a27d4694631f24352fb610025491`, November 2, 2026.
[Review](REVIEW.md), [grouped dispositions](findings.json),
[executed stages](test-verification.json), [method identities](method-ledger.json),
[selection only](selection-summary.json), [artifact integrity](evidence-integrity.json).

## Fresh affected checks

- Five new methods pass for profiles4/5/6: main packed PoolId/subscriber/tick
  corruption; independently mismatched residual Manager ticks; impossible,
  misaligned or noncanonical signed geometry; healthy both-leg proof without
  market reads; and source6 price-outage harvest/report/journal preservation.
- 75 affected existing operation-review/portfolio/policy-integrity methods pass.
  Existing wrong-owner/pool blockers, price outages, discarded simulations,
  journal immutability and current/historical compatibility retain coverage.
- Ten keeper-selection regression methods pass. The separate official focused
  inventory selects 842 methods and executes **zero** selected bodies; it is not
  an 842-method pass.

The union is **90 distinct passing methods across these scopes**, not a fresh
full Python/Solidity suite, operating rehearsal or published CI. Prior 119-method
and other historical campaigns are not added. The source-changing fix is limited
to the read-only operation report plus focused test selection; there is no change
to transaction submission, worker scheduling, receipt accounting or contracts.

## Causal control and preserved mistakes

The first three-method attempt incorrectly used the raw inert provider instead
of the report's pinned wrapper. It failed at an unpinned-code assertion, so its
23 failure entries are **not** evidence of the production defect. The first full
five-method run similarly retained 26 fixture failures. Both outputs are kept.

After correcting only that fixture construction, all five methods pass against
the repaired implementation. A separate isolated process executes the saved
original `operation_review.py` body with the corrected negative tests: three
methods produce 23 missing-guard assertions/subcases, zero errors/skips. Those
failures are the causal reproduction. The override path/hash is recorded apart
from current working-file pins. No original source/report was overwritten to
produce that control, and no failed attempt is counted as success.

## Historical reconciliation and unchanged source

The ten selected files are findings narratives; relevant verification/receipt
records and current mechanisms are checked as described in the matrix. This
does not claim a new reading/execution of all 352 narratives or all descendants
of the older 235-group ledger. Source5/4 results, source-specific test doubles,
gas traces, partial campaigns and old publication statements remain historical.

All 172 artifact entries checked across recognized manifest/copy formats match,
including ten explicit external-file references from the original five reports.
Three older families use stage-pin/receipt inventories rather than that manifest
format; the record explicitly notes this instead of silently claiming a full
artifact audit. All 222 selected historical/previous-consolidation files and four
protected dirty files remain byte-identical to this task's baseline.

All 83 exact compiler-input contents (52 production sources/31 dependencies)
still match normal-final-0a0cac9f06. The 43 normal size gates, current source-bound
471-context internal static review and 37-contract/826-function reference are
reused/checked without new Solidity tests, compilation or Slither execution.
Runtime margins remain Vault635/Budget237/Migration20 bytes at those exact pins.
No target-chain gas, dynamic argument or maximum-population acceptance follows.

## Final consistency and publication

The central ledger keeps task IDs/status/order and updates three existing
acceptance records; generated Todo remains the sole task checklist. Current
README, feature/evidence, roadmap, release boundary, operator/keeper guide and
repository memory point to this report. [Final checks](final-checks.json) record
generated reference/Todo, source/static reuse, changed-document links/anchors,
whitespace and exact staged Python publication closure.
[Manifest](artifact-manifest.json) binds this report's artifacts, excluding itself.

Raw attempts, originals, logs, source pins and helper scripts remain outside Git:
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/ten-audit-consolidation-20261102`.

No service/site/Anvil/NFT/LP/balance/journal/signer/heartbeat change or public
transaction/deployment/sealing occurred. Git publication is separate from rollout.
The two implementation gaps, actual providers/feeds/routes/VRF/authorities,
OpenSea/storage/source6 integration, gas/market/operating recovery and independent
audit/remediation remain open. Production remains **NOT APPROVED**.
