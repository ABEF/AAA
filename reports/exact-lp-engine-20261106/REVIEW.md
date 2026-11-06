# Exact-unit LP engine and keeper retry diagnostics

6 November 2026. Baseline main `b76dfcc5d1a2513ce6b277e43a6254eb63a74640`.
Production **NOT APPROVED**. This implements two bounded milestones from the
[sole Todo](../../TODO.md), following the [implementation scope](PLAN.md).

## Result

1. A real internal [Solidity allocator](../../src/libraries/ExactLPAllocation.sol)
   now assigns whole LP reward units to bounded, mutable NFT share weights.
   It settles both ETH/ZZZ paths before changing a weight and preserves old
   rights. It is **not connected to current Rewards/Vault/canonical accounting**.
2. The read-only [keeper review](../../keeper/operation_review.py) now reports
   matching local retry delays before simulation. It no longer describes an
   action as eligible while that recorded worker retry is still waiting.

No existing production contract ABI, creation code or runtime changed. The new
internal library changes no active module/profile. No deployment, service,
website, test-chain, signing or journal change occurred.

## Findings and implemented improvements

| Finding | Improvement | Evidence / practical limit |
| --- | --- | --- |
| Resetting rounding carry after every genuine share increase can repeatedly disadvantage the other branch. | Preserve a bounded high/low fairness phase; settle old money with old weights and rebase only the low remainder. No-op updates preserve all state. | Independent eager/rational checks, genuine-growth and full-width rebase cases. Phase approximation and hierarchical rounding remain explicit below. |
| A straightforward lazy tree writes the selected child to storage, then immediately reads/deletes it at the next level. | Carry that selected amount in memory; store sibling amounts and final leaf rights only. No external call can observe the temporary memory state. | Full-state differential compares all 2,047 node weights, both pending/phase books and outstanding totals after each action/preview. |
| The operation report ignored a saved, future action retry deadline. | Expose `checks.local_retry`; report `not_due` / `confirmed_revert_retry` before financial simulation, after pending/lifecycle/authority blockers. | 40 focused methods, including 10 new cases. No new RPC call or journal write. |
| One combined full-state scanner exceeded Forge's default per-test gas envelope. | Split at its existing second fresh-pair boundary, retaining every action/assertion and the other 15 successful methods. | Both final scanner methods pass the default limit; diagnostic higher-budget evidence remains historical. No production/config limit was raised. |

## Allocation design and boundaries

The tree has 1,024 leaves, with only immutable mint ordinals 1..1,000 admitted.
Random NFT IDs are not tree indices. One tree has exactly two books: native ETH
and fixed ZZZ. Root credit is constant tree work; previews, claims and weight
updates follow at most ten levels. Positive credit to an empty cohort rejects.
Outstanding amounts are uint256-bounded; no lifetime receipt counter can overflow
after previously received money has been paid.

Each split conserves its input exactly. Fairness phase is
`high/2^128 + low/(2^128 * subtreeWeight)`; it is not owed money. Fixed-weight
batching/materialization preserves exact rational split behavior. Genuine weight
changes keep high phase and rescale the low remainder using full-precision math.
Phase loss is less than `2^-128` per changed node. This **does not bound integer
payout distance**: sufficiently near a rounding boundary, even tiny phase loss
can delay one unit. Hierarchical rounding differs from flat largest-remainder
allocation. No optimal fairness or manipulation-immunity guarantee is claimed.

The primitive permits zero/decreased weights while preserving existing whole
rights. That does not authorize PoPL withdrawal, deactivation or ordinal reuse.
It contains no funding, owner, recipient, token movement or external-call logic;
the eventual host must enforce all of those boundaries.

The [developer guide](../../docs/EXACT_LP_ALLOCATION.md) defines required wiring:
one individual tree per logical bucket and one equal-activation collective tree
per currency, with atomic Vault/Membership synchronization. Main/residual legs
do not become separate share accounts; rarity, compound, buyback and royalty
books remain separate. Same-NFT conversion output must not be redistributed to
the current cohort. A fresh accounting/canonical/event/consumer boundary is
required; current accounting6/V8 rights cannot be relabeled.

## Measured engine improvement

Raw cold execution samples with 1,000 configured ordinals:

| Operation | Initial engine | Optimized engine | Reduction |
| --- | ---: | ---: | ---: |
| Root credit | 10,431 | 10,431 | unchanged |
| One-book claim materialization | 961,229 | 748,391 | 22.14% |
| Weight update with both pending books | 1,838,225 | 1,484,007 | 19.27% |
| 32 engine entries: 16 NFTs × two books | 3,808,651 | 3,008,245 | 21.02% |

These are harness `gasleft` samples with explicitly cold state, not complete
transaction/host gas, net refunds, network costs or approval of the 12M work
envelope. They omit future host authentication, funding, token calls, other
individual/collective trees and canonical consumers. The 62-byte library shell
does not measure future inlined host size. Integration gas and maximum-state
claim/canonical costs remain open.

## Keeper output semantics

`checks.local_retry` exposes availability, action key, normalized deadline,
state, remaining seconds and provenance. Valid legacy decimal-string counters
use the existing integer parser. Missing journals remain unavailable; a missing
entry in a matching journal is `not_recorded`, not a fabricated deadline.
The report reads bounded existing state for at most four buckets × three actions.

This is validated local scheduling evidence. The report does not independently
re-prove an old receipt, authorize execution or guarantee inclusion. Pending,
lifecycle and authority blockers retain priority. Disabled/inactive work retains
its earlier unconfigured/not-needed state. Worker logic, journal schema,
retry policy, signing and service installation remain unchanged.

## What is verified and still open

The [verification record](VERIFICATION.md) separates 17 distinct Solidity methods,
40 focused backend methods, normal gates, current static analysis and exact
reuse. Original failures, source stages and prior reports remain preserved.

Remaining accepted work is the complete LP ledger integration: authenticated
share/enrollment updates, funded liabilities and current-owner claims,
same-component conversions, explicit canonical export/import, event/replay/
checkpoint/API consumers and integrated runtime/gas review. Current LP fractions
are still active. Royalty4 exact tickets are independent and unchanged.

Qualified feeds/routes/VRF, authority selection, OpenSea, actual maximum operating
workload/storage/recovery and independent audit/remediation remain release gates.
Source publication does not qualify or modify any live environment.
