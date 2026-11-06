# Main/residual LP audit and implemented improvements

6November2026; baseline main `5d70b4b`. Production NOT APPROVED.
[Lifecycle/recovery matrix](LIFECYCLE.md), [plan](PLAN.md) and
[verification](VERIFICATION.md) separate current code, new evidence and limits.

## Findings and disposition

| Finding | Consequence | Disposition |
| --- | --- | --- |
| Fresh6 shared readers compared per-leg reported amounts with an aggregate but did not independently derive physical principal. | Correlated wrong views, or offsetting wrong leg amounts, could pass off-chain admission. This was not an on-chain withdrawal exploit; contract floors still apply. | Fixed: derive each leg from captured sqrt price, rounded ticks and actual PosM liquidity, then reconcile each leg and total. |
| Stable fingerprint was checked only for nonzero; residual containment was not verified in that reader. | Wrong nonzero identity or non-contained residual data could be accepted despite contradicting the fresh source's physical model. | Fixed: reconstruct the complete packed-info stable identity and liquidity-sensitive hash, authenticate both and reject impossible containment. |
| An extra structural proof could duplicate contribution-review RPC work. | Unnecessary read cost and another independently handled intermediate value. | Refactored private proof reuse. Public portfolio payload unchanged; fresh shared reads add one same-block hash getter per bucket, while contribution context uses the already verified result instead of reading it again. |
| Documentation could imply that only rebalance opens a residual, or that every replacement uses keeper timing. | Operator may unintentionally recreate two positions during resume/move, or misunderstand recovery timing. | Clarified: governed move/resume also use normal replacement execution under destination mode, without ordinary keeper timing; financial/custody guards remain. |
| Destination-hybrid move/resume composition lacked focused actual-core evidence. | Earlier movement examples ended at a single destination and did not establish this particular two-leg sequence/rollback. | New actual-local-v4 scenarios cover destination ON, resume→activation/growth→OFF merge and infeasible-destination atomic rollback. |

The pure amount function is extracted unchanged from the existing preflight into
a small neutral helper. Its old entry point delegates to it; historical5 reader
behavior remains explicit. This is separate from the new fresh6 admission rules.
No production Solidity, allocation, permission, range policy, clock or financial
limit is changed. Fee-only harvest diagnostics remain independent of spot/USD.

## Lifecycle conclusions

Enabling mode creates nothing immediately. The residual can be created during a
whole ordinary replacement, governed same-pair move or parked resume when the
destination mode is ON and useful inventory/geometry permits it. Initial entry,
main growth, standalone compound and emergency single consolidation do not
independently create it. Enabled without an auxiliary ID can be valid.

Both positions remain in the same logical share account. Fills, reversals and
main-only contributions change composition/value, not the two-position bound.
The next whole replacement closes every old registered leg before creating its
new one/two positions. Disabled mode retains an existing residual until actual
merge or raw close. A failed replacement preserves old custody and backing.

Residual-only closure harvests both but removes only the residual. Its principal
becomes attributed idle, leaving main/shares/clock/mode intact. It does not release
compound or pay governance. An idle ceiling can block new entry until guarded
reinvestment/recovery; that is not permission for an operator sweep or entrant
subsidy. Global pause and unpause are separate from deployment and desired mode.

No ordinary custody, forgotten-leg, share-conservation or duplicate80/10/5/5
defect was confirmed in the reviewed qualified-token model. That is a bounded
internal review, not proof over all markets, dependencies or transaction inputs.

## Open dependency and economic boundaries

1. Pre-close collection and subsequent burn receipts are separate operations.
   A malicious/upgraded token or compromised periphery callback could generate
   fees in that gap, including on a residual still open while the main closes.
   Current burn receipts can then include late fees in principal rather than
   split them80/10/5/5. No ordinary outside transaction can interleave inside the
   atomic close with conventional ERC20 and reviewed hookless dependencies.
   Actual ZZZ source/proxy/admin/callback and periphery qualification is required;
   supporting that broader behavior needs an explicit reviewed accounting design.
2. Attributed idle, temporarily uneconomic execution and permanently broken
   tokens/core/chains are different states. Raw close/park/terminal return avoid
   ordinary USD or swap dependencies but cannot guarantee movement through a
   permanently broken asset or venue. Earned/reserve liabilities must not vanish.
3.60/40 placement is not continuously maintained or proven optimal. Inactive
   residuals, adverse selection, IL, repeated allowed loss and MEV remain economic
   exposure. Existing sampled confirmation and jitter are not MEV immunity.
4. Matching fresh services/site, actual feeds/routes/token/VRF, maximum-state gas,
   operating restart/restore/provider reliability and independent audit remain
   release gates. Served current3 cannot be relabelled as this fresh6 reader.

Actual token-source qualification was not closed by third-party labels/search
results or an inaccessible explorer page. The dependency Todo keeps that work
open; no wallet, key, public transaction or live service was used for this audit.

## Publication boundary

The central Todo, features, operator manual, current context and relevant guides
are aligned with these results. Historic report bytes retain their source scope.
Existing Anvil holdings, dist, journals, signer, sites/services and paused
heartbeat remain unchanged. Source publication is not a rollout or approval.
