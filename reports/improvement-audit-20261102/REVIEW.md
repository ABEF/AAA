# Audit, fixes and consolidation

Reviewed November2,2026, Europe/Paris, starting at main44f2192. The
[improved request](PROMPT.md) expands the vague request into concrete accounting,
data, keeper, configuration, recovery and verification boundaries. Existing
source6 financial rules and deployment boundaries remain unchanged.
[Verification](VERIFICATION.md) records actual executed/reused evidence.

## Findings and repairs

| Finding | Impact | Implemented correction |
| --- | --- | --- |
| Inventory custody checks weaker than NFT detail | Collection/wallet summaries could accept shares greater than bucket supply or a parked NFT paired with an active group, then present valuation as unavailable while continuing financial totals. Distinct individually valid shares could also sum above bucket supply within a chunk. | Extract existing detail custody proof into one shared reader. Apply it to bounded current3–6 collection/wallet chunks, checking every NFT and the partial share sum. Cache group/supply only within the same pinned request; the sum check adds no RPC. |
| Governed buyback cap confused with constructor provenance | A legitimate post-seal cap change failed source6 preflight, encouraging an incorrect rewrite of creation history. | Require current `chains[].buyback_maximum_usd18`, bind it to the pinned live `maxTradeUSD()` getter and compare the operating limit to it. Keep the original constructor maximum separately and unchanged. Missing current declarations fail before RPC. |
| Maintenance policy omitted from health validation | A source6 record with missing, malformed or impossible maintenance policy could still produce no confirmation-health reasons. | Validate exact Policy1 record shape/domain, version, address, revision, bounds and recomputed scoped fingerprint. Historical profiles retain their own shape. Health remains local diagnostic evidence, not chain authentication. |
| Missing idle-policy read did not block an operation report | A transient policy fault could leave an operation marked eligible despite an unknown required idle ceiling. | Report `maintenance_idle_policy_unavailable` and skip principal-operation simulation. Independently eligible harvesting remains separate. No scheduling/financial policy changes. |
| Focused keeper selection omitted current safety cases | The explicit focused runner omitted source5/6 portfolio/policy tests despite full Python discovery containing them. | Include those modules and new integrity tests; add an inventory regression proving reachability without executing selected bodies. Inventory counts remain distinct from test passes. |
| Nested Python locals mistaken for package exports | The Git publication check could overlook a missing module if a package initializer contained a same-named function/class/comprehension local or a nested `__getattr__`. | Scope possible package bindings without descending into nested scopes. Keep actual module exports and published namespace modules valid; execute no initializer. Dynamic behavior remains outside static closure assurance. |
| Required source inventory omitted current helper classes | Source consistency could pass after standalone Policy/Portfolio sources disappeared, or report an outdated required-helper inventory. | Include all current source classes, cross-check against the compiler-bound callable inventory and add actual temporary source-removal negatives. Optional Pyth deployment and repeated route-helper instances remain different from required source-class counts. |
| Current navigation/limits contained stale claims | The Todo still quoted old39-gate/37-byte/59-byte limits; component/manual text called Portfolio2 Policy1 and operation prose implied a fixed60/40 allocation. | Replace current prose with exact reused43-gate source facts and configured allocation semantics. Preserve historical reports and their original metrics. |

## Preservation and behavioral boundaries

The shared custody reader preserves existing NFT-detail semantics. Stronger chunk
validation intentionally rejects contradictory evidence; it does not turn a price
outage into a zero balance or disable verified owner/raw funded claims. Additional
reads are bounded: group/supply per unique bucket per request, shares per NFT.
Caches are neither global nor cross-block; budgets are not raised automatically.
The separate request-local partial sum must also fit the bucket denominator;
it does not presume the request contains every NFT or redefine share ownership.
Terminal principal remains separate from LP/royalty income and claimable rewards.

The new inventory declaration is a current reviewed value, not new governance
authority. Fresh schema8 records without it must be completed from reviewed
observations; constructor history must not be edited. Old profiles remain explicit
and unchanged. The example stays null/unqualified, never a fabricated deployment.

Health/report corrections add no signing, transaction, configuration, nonce,
reset, fee or custody authority. Preserve existing journals/pending-first recovery;
do not repair evidence by deleting fields or inserting guessed values. Any later
source/writer/checker rollout must follow the separately authorized procedure.

No production Solidity changed. ETH/fixedZZZ inputs,80/10/5/5, rarity royalties,
per-NFT current-owner rights, default2/1/3% limits, hard ceilings, trigger/timing,
one/two-leg custody and terminal holder return remain unchanged. This is not an
LP exit instruction. No service/site/Anvil/journal/signer/heartbeat or public
transaction/deployment/sealing change occurred.

## What this review does not resolve

Actual independent feeds, conversion/execution routes, VRF/provider controls,
authority addresses, OpenSea integration, target gas/economics, source6 website/
services, off-host recovery and independent audit remain release requirements.
Shared validation and coherent block reads cannot prove an RPC provider honest
or logs complete. A stored fingerprint is not attestation of a running keeper.
Strict required reads may make a report unavailable; they must not be bypassed
to restore apparent availability. Added work still needs actual latency/load
qualification under existing finite budgets.

The scope is concrete repairs and their reachable interactions, with exact-source
reuse of the prior Solidity audit. It is not a new exhaustive full-project test
execution or a guarantee that all bugs/adversarial market strategies are absent.
