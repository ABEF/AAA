# Principal, price and venue adversarial review

This partition reviews12concrete contracts and190callable ABI rows, including
constructors, generated getters and native receive hooks. The
[function matrix](principal-review.json) records588scenario instances across38
families. Those are **static review cases, not588tests or proof that every
schedule has been executed**. No production source, service, signer, test chain,
wallet, balance, journal or financial parameter was changed by this partition.

## Paths traced

| Feature | Unusual/adversarial cases considered | Result and limit |
| --- | --- | --- |
| Source admission | Alternate/repeated ZZZ, native sentinel confusion, disabled token/feed, pool versus source versus royalty currency, duplicate factory child | One fixed ZZZ/native identity; enablement and current pricing remain separate. `isContributionAsset` intentionally still identifies disabled ZZZ; `value` rejects positive disabled input. |
| Original-source Entry | Wrong owner/operator/route/deadline/value/minimum, stale approved route, callbacks during pull/conversion/approval/reset/refund, force-sent prefunds | Exact live owner/Vault call context and original price vector bracket all Entry callbacks. Unsupported/partial/infeasible execution reverts; no arbitrary recipient/executor was found. |
| USD bounds and Pyth | Invalid signs/precision/round/time/code, stale or failing second source, sequencer down/recovery, malformed/oversized/gas-heavy upstream response, confidence/exponent edges | Bounded static reads and conservative integer bounds fail closed. Two agreeing sources are not proof of independence; proxy/admin/updater qualification stays open. |
| Marginal LP and shares | Zero/near-zero or historical NAV, tiny/huge/packed values, incumbent idle/compound, late old-currency reserves, donation, entry-swap income, out-of-range joins | Fixed phases, old-weight checkpoints and factual deployed-LP deltas separate new capital from incumbent backing. Invalid/zero/oversized share issuance reverts. Source agreement can be healthy while execution is infeasible. |
| Physical venue custody | Wrong owner/key/ticks, changed LP during callback, token taxes/rebases, native debt/prefund/refund, Permit2 approval reset, partial swap deltas, duplicate callback | Fixed typed actions, authenticated one-shot callback hashes, exact raw balances and final LP/spot facts protect the measured operation. These checks cannot make a lying/upgradable token or approved malicious venue trustworthy. |
| Range/maintenance | Inverse-price orientation, negative/exact tick spacing, min/max representability, flat-price configuration changes, fee directions, cooldown, adaptive-rule drift/flip-flop | Keeper selects only the reviewed width under the on-chain rule; physical replacement remains a separate guarded rebalance. Width/polling does not guarantee continuous in-range fees or a next execution time. |
| Harvest/compound | Frequent small harvest, stale pricing, donated actual pool fees versus raw Vault prefund, callbacks and failed redeployment, no compound reserve | Receipt-backed harvest remains distinct from new principal, individual/collective claims and5%jobs. Attributed idle can be reinvested without issuing shares; failed maintenance rolls back. |
| Movement/canonical boundary | Alias capacity, paused parking, normal/raw exit, exact return, unsupported actual pair, source versus whole-collection migration | Fixed-module checks remain; raw exit is separately approved and not a general holder/admin sweep. External custody is trusted; source cannot force return or relocate NFT rights by sending LP assets alone. Full handoff callable review is the governance partition. |

No new unprivileged principal-theft, fabricated-share or loss-limit bypass was
confirmed in this partition. This is a bounded source review, not an independent
audit or a global absence-of-vulnerability claim.

## Evidence reuse and coverage precision

The production sources match the source-bound callable reference and prior
[market/v4 bindings](../market-adversarial-20261026/bindings.json). The unchanged
[15composed integration methods](../market-adversarial-20261026/solidity-summary.json)
are reused at their original scope: actual installed local v4, explicit admission/
governance/feed/VRF/Permit2 substitutes. They include directional out-of-range
activation/growth and rebalance/claims, donations before newcomer entry, thin-depth
and callback failures, and complete fee/claim/backing compositions.

The matrix separately lists relevant existing test source files as review aids;
their existence is not represented as fresh successful execution. No unchanged
Solidity/static/full-regression suite was repeated. Generated getters are checked
for actual ABI/default/identity semantics instead of assigning them fictitious
transaction-reentrancy cases. Private helpers and relevant base/library/companion
interactions are recorded separately from the owned190callable rows.

## Operating and economic limits retained

- A3% lower-denominator source-agreement band does not waive the2% conservative
  upper-input/lower-deployed budget. Spread alone can make a contribution fail;
  conversion and placement costs tighten availability further.
- Per-operation maintenance/conversion limits do not cap gas, impermanent loss,
  market movement or cumulative turnover. The accepted per-operation-only policy
  was not replaced by an unapproved cumulative cap.
- Near-unrepresentable ticks, uint128 raw bounds, the share-supply ceiling,
  zero NAV and high admitted-dependency gas can stop operations. No arbitrary
  rescaling, stale price, asset sweep or guessed-zero recovery was added.
- Runtime checks do not pin mutable proxy/admin storage or prove token honesty.
  Real independent feeds, current liquidity/fees/routes, ETH settlement, actual
  operating costs and external recovery rehearsals remain release requirements.
- Ordinary `live` pause checks are entry checks; preparation/canonical/governance
  guards have their documented callback rechecks. A privileged party executing a
  pause inside its own callback is not an unprivileged authorization bypass.
  Confirmed reads are taken after transactions; transient callback-readable NAV
  is not a qualified cross-protocol collateral oracle.

## Independent review of root RPC changes

Read-only review of `zzz_ops/rpc.py` and `test_rpc_integrity.py` found no concrete
regression in the new strict decoder/canonical chain-quantity behavior. Duplicate
fields at every object depth, nonfinite values, parser recursion limits and
ambiguous result/error envelopes now fail inside sanitized bounded failover.
Finite fee-history floats, uppercase hex digits, checked integer chain-ID return,
the existing read-only method allowlist and terminal WorkLimit propagation remain.
No contract/API profile or signer change is necessary for rejection of malformed
wire responses. This independent review did not repeat root's focused tests.

Further activation/trace/gas composition reading found no additional reproduced
defect: required source/price/config pins, same canonical hash, complete two-pass
trace agreement, actual LP measurement, captured caller maximum, exact approval,
gas/value affordability, snapshot expiry and final block verification remain.
These are observations from a provider, not cryptographic execution proofs or
qualification of a production RPC.
