# Internal liquidity-operations review - 2026-10-25

Read the [accepted scope and verification plan](PLAN.md) and
[exact evidence/limitations](VERIFICATION.md). This reviews an undeployed
candidate, not deployed funds or a completed independent audit. Production
**NOT APPROVED**. Publication has its own receipt.

## Findings and changes

| Finding | Resolution and security boundary |
| --- | --- |
| A single pre-swap balance plan can leave avoidable post-swap ratio idle | Re-plan once against actual post-swap state, maximum two swaps. Skip corrections<=1bp of available input. Keep raw deltas/approvals, final price/policy, incumbent fees and marginal deployed-LP checks. No arbitrary router, unbounded optimizer or guaranteedzeroidle. |
| Attributed idle could not be intentionally compounded without fresh reserve | Existing compound path now accepts the bucket's own idle, captures fixed starting prices/principal plus actual released compound, preserves the maintenance floor and5% idle ceiling, and has a successful-operation cooldown. No extra recipient or sweep. |
| Raw ETH/ZZZ ratio and “ZZZ price in ETH” describe different endpoints and triggers | Explicit version1 orientation preserves historical raw mode0 and opts into inverse mode1. Endpoints round outward. Target/trigger/planner/API use the selected orientation consistently; oracle/spot validation still guards the actual raw market. No reinterpretation of physical LP or old deployments. |
| User wants keeper choice, but arbitrary range authority is unnecessary | Governance reviews a default-disabled two-width policy, thresholds, cooldown and non-width configuration fingerprint. Keeper provides only the pool; Strategy chooses2500/5000. A narrow fixed-Strategy Registry callback changes only width. Physical movement remains the normal separately guarded rebalance. |
| Keeper reserve thresholds mixed currencies' raw economic meanings and omitted idle | Optional positive per-currency thresholds, explicit cooldown, reviewed Budget bindings/version and attributed-idle reads replace guessing. No ETH/ZZZ raw-unit sum or contract-balance sweep. Legacy reserve-only mode remains explicit compatibility, not recommended economic policy. |
| Keeper still scheduled removed bridge actions | New bridge scheduling and nonempty legacy route configuration are rejected. Saved pending receipt recovery still runs first; original hashes, reviews and budgets are not deleted, resent or relabeled. |
| Runbooks treated optional future-chain systems as mandatory release work | Current scope is source-chain custody only plus guarded same-pair local moves. Custodian performs any external bridge/issuer exchange. Same-chain whole-collection handoff remains; remote NFT/reward relocation and post-halt recovery are not supplied. Schema5 capability output now distinguishes supported local custody from disabled legacy bridge status. |

Contribution default changes **only** from1% to the user-approved2%; LP/royalty
conversion stays1%, ordinary maintenance3%, gas separate. Existing immediate
governance maxima remain10%. Retained idle is principal, not execution loss,
but cannot satisfy marginal **deployed** LP. The conservative source/final
guards are not replaced by a nominal 98% arithmetic promise.

The related local rehearsal generator had stale floor anchors and a hardcoded
1% manifest. Its source-anchor/default derivation and test guard/growth fixture
are corrected without changing production sources or re-running a complete
runtime rehearsal; the separate Python/generation/typecheck evidence records
that narrower scope.

## Review of control and accounting interactions

Root review checked Vault/Budget conservation, bounded swaps, real physical LP,
harvest-before-increase, fixed-price checkpoints, cooldown rollback, exact native/
token spending and prefund exclusion. A second reviewer inspected Strategy's
two-width authority, configuration pinning, orientation/rounding, lifecycle and
separate selection/rebalance boundary. Backend review checked explicit profiles,
pinned-block reads, strict ABI/policy validation, inverse trigger recomputation,
historical version0 handling and typed event/catalog preservation. Keeper review
and focused transcript checks are recorded with their final source scope below.

No new generic executor, arbitrary token recipient, holder redemption, sweep,
claim haircut, unbounded keeper width or governance bypass is introduced by
these changes. This is a limited code-review finding, **not proof of absence of
exploits**. Immediate governance can still approve dangerous dependencies or
external custody; a custodian can divert funds and the source cannot force return.

## Size and gas decisions

The initial Vault draft and Registry callback drafts exceeded normal size limits
and were rejected. Shared internal placement logic removed duplication; the
Registry reuses the actual immutable controller's sealed/canonical module
authorization plus explicit pause/preparation checks before local-only writes.
There are no state-changing external calls afterward. The only authorized
Strategy emits the complete old/new/review selection event after callback success,
so a redundant Registry event was removed. No authority, config, funding, loss,
runtime/initcode or gas guard was removed to make a build pass.

Final Vault and Registry remain close to normal limits. Future Entry/Registry
work must account for embedded creation code; adding a field or helper is not
size-free. Use exact final [size and gas receipts](VERIFICATION.md), not earlier
passing snapshots. Actual two-pass fixture gas and substituted maximum-state
cold gas have different scope and cannot be combined into a proven production
maximum. Do not increase limits to conceal an infeasible design.

## Open economic and release boundaries

- **Review-time contribution cap remains unbound in current Request (A-08).**
  Execution captures current policy; it does not sign the earlier displayed
  percentage. Governance can change the cap before inclusion. Caller raw minima
  remain, but do not establish the earlier USD percentage. The versioned caller-
  bound Entry/API/wallet path remains required before public activation signing.
  Strategy orientation/range policy is also mutable operating state, not part of
  the frozen USD snapshot or a signed configuration commitment. A reviewed API
  snapshot does not lock later inclusion to those settings; ordinary value/venue
  guards still apply and unprivileged callers gain no configuration permission.
- Actual depth, ticks, conversion routes, dual independent feeds and full transaction
  cost must qualify each input. The corrected local shallow fixture does not
  guarantee every $100 activation or $5 top-up will be executable.
- The adaptive signal is displacement from the last applied oracle center, not
  measured continuous volatility or proof of a long quiet period. Thresholds,
  narrowing/widening economics, cooldown, MEV and gas need real-market review.
  Selection and actual rebalance take separate transactions; either can be delayed.
- Per-operation caps do not cap cumulative turnover/loss, impermanent loss or
  later price movement. The user explicitly retained no cumulative breaker.
- Classify idle, fractions, fee dust, reserves and quarantines under
  [the ownership guide](../../docs/IDLE_AND_DUST.md). No general clear-all is safe
  merely because a balance is small. Unsupported accidental assets may be stuck.
- No integrated bridge is needed for the selected custody workflow. External LP
  movement neither relocates NFTs/reward ledgers nor guarantees continued remote
  revenue. Unsupported immutable capabilities cannot be added by a config edit.
- Actual chain/services/keys, OpenSea/VRF, native website integration, complete
  max-state venue gas, operating rehearsals and independent audit/remediation
  remain open. Public signer stays Anvil-only; public DEPLOYMENT stays null.

Existing8902/Anvil/NFT/LP/balances/journals/dist repair overlay, website source/build/
server and paused monitoring are preserved. No public transaction, deployment,
sealing, service action or monitor restart is part of this work.
