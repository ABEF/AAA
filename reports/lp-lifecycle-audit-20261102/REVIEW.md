# LP lifecycle, reward allocation and mode-transition review

Reviewed 2 November 2026. Internal source review, not independent audit or
production approval. Base main: `846ccd1ff3576412c1fec36c52a93bc573af5855`.
The [verification record](VERIFICATION.md) separates fresh checks, failures,
fixture corrections and exact-context reuse. Earlier reports retain their bytes
and original scope.

## Material findings and corrections

| Finding | Evidence and consequence | Correction |
| --- | --- | --- |
| Ordinary routing ranked candidates without proving the new main would be active. | Real local v4 quotes selected tick -403 in single mode and -401 in hybrid mode for a main beginning at -400. Final mint checks correctly rejected them. That protected capital but could block a valid alternative execution. | [Balancer](../../src/ZZZLPBalancer.sol) filters physical viability before ranking ordinary replacements. [Manager](../../src/ZZZLiquidityManager.sol) uses this path for both modes, with captured prices and floor10000 for single or the governed hybrid floor. Final mint checks remain. |
| A sqrt-price-only activity test would misclassify an initialized downward crossing. | At the exact lower sqrt, core may store lowerTick-1. The position is then inactive even though sqrt comparison alone appears to pass. | The actual quote returns the stored core tick. Compare sqrt at that stored tick with the proposed bounds; do not reconstruct a tick from sqrt. Self-only quote callbacks validate the exact100-byte revert and signed tick domain. |
| Previous harvest diagnostics overstated source independence. | `LiquidityManager.ticks` forwards through the position child to the same packed PositionManager identity. Comparing those getters is not an independent stored-range proof. The previous ten-report narrative and test name implied otherwise. | Preserve identity/ownership/geometry coherence checks and price-outage harvesting; explicitly return `geometry_sources_independent:false`, correct the test name, and correct current guides. Historical reports are preserved, with this correction superseding their independence claim. |

Ordinary no-swap baseline must also be physically active. A different swap venue
cannot reactivate an already-inactive destination, so it is excluded in that
case. A swap in the destination may restore activity; target-pool overshoots
shrink the search, while trades not yet reaching the range increase it. Candidates
still satisfy existing output, price, known-fee/additional-loss and context guards.
The search remains bounded and does not prove a global optimum.

Initial contributions, growth, existing-main compounding and explicit emergency
use their existing separate policies. This repair does not add ordinary
replacement restrictions to the approved outside-range entrant flow. The final
active-main pre/post-callback checks remain authoritative even after a good quote.

## Portfolio and reward lifecycle established by the composed checks

- **One logical account, at most two physical legs in the same pool.** Both are
  Vault-owned; per-NFT shares refer to aggregate attributed NAV, not raw liquidity
  added across different ticks.
- **Enabling is permission, not an immediate trade or a forced60/40 allocation.**
  A naturally sufficient main can remain single with applied mode enabled.
- **Disabling requests a guarded merge.** It neither deactivates NFTs nor closes
  or forgets the residual. Both actual legs remain valued and harvested until
  replacement succeeds. Failure preserves backing, shares and unclaimed rights.
- **Mode reversal still has a pending revision.** Enable-disable-enable does not
  revive old confirmation or skip the guarded adjustment.
- **Revenue follows actual receipts.** The composed hybrid/entry/disable/harvest/
  partial-claim/merge sequence checks exact80/10/5/5 allocation for ETH and ZZZ,
  including carried split dust, reward liabilities and compound/buyback reserves.
  Alice's partial claim does not reduce Bob's rights; later harvest and Bob's
  claim remain consistent across the merge. Activated membership remains2.
- **Claims are not maintenance.** They spend funded liabilities; they do not
  redistribute the pool, compound, burn, recenter or deactivate another NFT.

These tests exercise actual v4 core/periphery with isolated synthetic admission,
prices, identities and test funding. They do not establish live-market returns,
all possible inputs, provider honesty or target-chain acceptance.

## Interface, size and operator impact

The undeployed typed helper replaces `planPartial` with `planReplacement` and
adds the stored tick to its self-quote result. The generated [callable reference](../../docs/CONTRACT_FUNCTIONS.md)
is refreshed. The eight-word accounting6 record and existing profile version
constants remain; matching record shape/version alone never authorizes a runtime.
New bytecode, constructor/runtime pins and reviewed deployment configuration are
required. Existing deployments and journals cannot be relabelled or upgraded by
editing JSON.

No operator wallet call changes: use reviewed Policy setters and guarded
`Vault.rebalance`, or the explicitly paused manual recovery procedures. The
[operator lifecycle table](../../docs/OPERATOR_MANUAL.md#portfolio-mode-states-and-reward-effects)
states exact desired/applied/physical-leg outcomes and failure handling.

An initial inverse-tick implementation exceeded the normal Balancer runtime
limit by377bytes and was rejected. Stored-tick comparison reduced the final
runtime to24216bytes, with360bytes headroom. All43 normal runtime/initcode gates
pass at the exact new closure. Vault635/Budget237/Migration20 runtime margins
are unchanged and remain tight. This fix adds a safeguard; it does not claim
smaller bytecode than the base Balancer or target-chain gas qualification.

## Remaining limits and priorities

1. Bounded quote sizing can still fail on real depth, fees, gas or narrow residual
   gap/rounding geometry. Passing main activity alone does not prove residual
   feasibility. Keep atomic failure and final floors; qualify representative
   venues and inventories without an unsafe automatic fallback.
2. Review real dual feeds, routes, RPC, randomness, authorities, OpenSea, source6
   consumers and operating/recovery rehearsals. Local synthetic evidence cannot
   close those gates. Independent audit/remediation remains required.
3. Lifetime verified-history scaling remains open. Do not replace authenticated
   replay with unsigned cached totals or silently drop predecessor history.
4. Preserve separated policy domains: gross loss, additional execution loss,
   oracle agreement, main floor, idle ceiling, caller floors and timing protect
   different conditions. This fix relaxes none of them.
5. The60% main floor is an approved policy tradeoff, not a demonstrated optimum.
   Residual inventory can drift, fill, become mixed or remain outside. No MEV
   immunity, uninterrupted sampled history or guaranteed maintenance liveness.

No allocation, ownership, custody, governance, loss default, timing default or
royalty rule changed. No deployment, public transaction, service/site rollout,
Anvil reset, signer/journal adoption or heartbeat change was performed.
