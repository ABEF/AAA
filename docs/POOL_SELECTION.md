# Selected Robinhood ETH / ZZZ pool

## Selected integration target

The selected integration target is the existing pool
`0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`.
This supersedes the Pons and proposed 0.30% targets. Pool selection is not release
approval; the recorded observation below is not a live price or depth claim.

| Property | Verified selection |
| --- | --- |
| Chain / venue | Robinhood 4663 / Uniswap v4 |
| Physical currencies | Native ETH / ZZZ `0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a` |
| PoolKey | `(address(0), ZZZ, 10020, 200, address(0))` |
| Hook | Zero; no Pons or custom hook |
| LP fee | Static 1.002% |
| Observed protocol fee | 0.1% per direction; separately controlled by Uniswap |
| Combined observed fee | Approximately 1.101%; gas/interface fees separate |

[Pinned observation](../reports/hookless-pool/observed-pool.json) includes the
initialization transaction, recomputed pool identity, dependency runtimes and wiring.
Reproduce with `scripts/verify-hookless-pool.py`. Active liquidity units are not USD
TVL or a volume forecast. Protocol and LP fees compose sequentially with rounding.
The creator cannot change this static fee or add a hook, but may remove their own
LP; token permissions, market depth and external governance remain separate risks.

## Admission and revenue

`SELECTED_NATIVE_POOL` records the launch identity. Governance can also use
`configureNative` after sealing for future initialized static, hookless native
ETH/ZZZ fee tiers on the same pinned Robinhood core. It checks the real slot fee,
code/wiring, admitted native/token assets and feeds, and existing strategy bounds.
Native admission and accounting no longer consult WETH or its proxy policy.
No dynamic fees, custom hooks or other native tokens are admitted. WETH/ZZZ uses
ordinary hookless `configure`. Exactly one pool accepts contributions at a time.

The accounting-3 candidate uses native ETH at the venue and throughout
principal/fee/reward custody; it does not normalize ETH to WETH. It preserves
prefunds, requires exact declared payable budgets and clears exact ERC20 allowances. Vault harvests before increasing LP so old
native fees cannot silently pay new principal. Unexpected offsets fail atomically.
Ordinary venue fees earned by PoPL's own LP receive the unchanged 80/10/5/5 split.
Creator-payment inboxes and hook-revenue intake are removed, not optional launch
services. Actual venue fees from PoPL's own liquidity fund the allocation.
Royalties stay separate; ZZZ-side holder fees still require reviewed ETH conversion.
The default reward-conversion loss cap is 1%, gas separate; governance can
change future conversion policy within its 10% ceiling. At the 1% default, the
recorded approximately 1.101% selected-pool fee does not qualify a full ZZZ reward
conversion at reference prices. A cheaper approved route is required; do not
silently widen a review or relabel backed ZZZ as converted ETH.

## Native admission and settlement safeguards

`configureNative` verifies Robinhood chain 4663 and the pinned Core,
PositionManager, StateView, Permit2 and fixed ZZZ runtimes/wiring. Initialized
slot state must match the static PoolKey fee. Dynamic fees, custom hooks, other
native pairs and mismatched source ZZZ fail closed. `accounting` and
`isNativePool` recheck native venue bindings; `get` returns stored configuration.
All preserve the real `address(0)` currency identity. There is no wrapper-valued
native-asset alias to use as an alternative identity.

LiquidityManager uses exact declared native budgets, actual LP ownership/key/
ticks/liquidity and measured balance deltas. It preserves its own and the
PositionManager's prefunds, clears exact token/Permit2 approvals and refunds only
the unused authenticated budget. Vault harvests before increasing LP, preventing
older native fees from paying new principal. Unexpected offsets, partial fills,
malformed callbacks and unrelated ETH cannot create principal or earned fees.
Collection/close sends authenticated core credits to Vault; actual fees are
classified separately from principal and reserves. Changed Uniswap protocol
fees do not by themselves freeze collection/close; swaps still require actual
net outputs and all configured minima.

Native principal custody, raw exit and exact native return do not call WETH.
An operation explicitly using a reviewed WETH/v3 conversion route retains that
wrapper/proxy dependency; native admission does not prove its safety. A broken
pool, token or recipient can still prevent settlement. No universal sweep or
withdrawal is provided. [Native architecture](NATIVE_ETH_ARCHITECTURE.md) covers
the full custody and ledger boundary.

## Move funds versus exit

| Intent | Operation | Boundary |
| --- | --- | --- |
| Another fee tier with the identical actual ETH/ZZZ pair | `Migration.moveFunds(bucket,pool,minimumLiquidity,deadline)`; the obsolete Migration `movePool` alias is removed | Atomic actual destination LP; unchanged NFT shares; one captured aggregate maintenance cap (3% default, governance maximum 10%), gas separate; no external custody. |
| Send principal to your regular address | Approve request, globally pause, then `Migration.exit(id)` | Normal mode converts all attributed principal to configured ZZZ before sending; recipient custody is explicitly trusted. |
| Swap impossible / prices unavailable | Separately approve `rawExit=true`, then `exit(id)` | Transfers attributed native ETH/ZZZ under raw close minima; no 3% USD guarantee; never automatic fallback. |

ETH and WETH are distinct currencies. Atomic moves between their pools remain
unimplemented and are rejected; they need a reviewed explicit conversion boundary.
Different-pair returns through separately approved external custody remain a
manual path, with actual new-token funding and destination LP checks. Moving LP does not silently enable destination deposits or alter
routes. [Exact operator steps](GOVERNED_CUSTODY_HANDOFF.md#move-funds-without-external-custody).
The aggregate maintenance cap defaults to 3% and governance can change it up to 10%
after sealing. Existing stricter pool/caller limits remain. Normal custody plans
retain their original absolute floor; explicit raw exit is a separate risk approval.
Native raw exit/recovery do not call WETH, but still depend on actual core/token
bindings, successful settlement and recipient transfers; there is no universal
exit guarantee through failed external dependencies.

## Remaining qualification

The selected pool fee applies only to the swapped portion of a contribution.
The default contribution budget is 2%, requiring at least 98% of conservative upper
input value as actual new LP; caller-bound policy and full execution checks still
apply. The separate 1% reward-conversion cap requires a cheaper qualified route. Independent ZZZ/USD pricing,
ETH/ZZZ contribution and reward-conversion routes, any optional royalty-currency
conversion, full execution/gas economics, production inventory,
VRF, authorities, marketplace support, operating rehearsals and independent audit
remain open. Bounded post-seal request/buyback controls and typed v4 conversion are implemented;
actual provider/market qualification remains open. Atomic ETH/WETH different-pair
movement is unsupported; explicit external custody remains a distinct trusted path. Existing fork observations
retain their original WETH-accounting source scope; local native fixtures do not
qualify live services. Fresh accounting-3 / fee-intake-1 / governance-2 runtime pins and actual native
wallet/service acceptance are required. Historical native-2 website reads do not
qualify current-3 integration. Existing fixtures/journals keep their original
profiles and public deployment is null.

[Native candidate evidence](../reports/native-eth-port/VERIFICATION.md) |
[Earlier selected-pool evidence](../reports/hookless-pool/VERIFICATION.md) |
[Sole Todo](../TODO.md#task-pons-qualification). Public signing stays disabled;
contracts are undeployed and production remains NOT APPROVED.
