**Current policy, 2026-10-24:** [Typed v4 conversions](TYPED_V4_ROUTES.md) and
[governed execution-loss limits](EXECUTION_LOSS_POLICY.md) are implemented in the
undeployed candidate. Defaults are 1% contribution, 1% conversion and 3% maintenance;
immediate governance may set each category up to a hard 10%. Existing stricter
venue/caller minima remain. Pending normal custody approvals retain their original
absolute floor. Earlier fixed-cap or v3-only descriptions below retain their
historical/default scope. Actual routes, services and independent audit remain open.

# Selected Robinhood ETH / ZZZ pool

## User decision - 2026-10-24

The selected integration target is the existing pool
`0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`.
This replaces Pons and the earlier proposed 0.30% pool. Selection is not release approval.

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

The native-accounting V2 candidate uses native ETH at the venue and throughout
principal/fee/reward custody; it does not normalize ETH to WETH. It preserves
prefunds, requires exact declared payable budgets and clears exact ERC20 allowances. Vault harvests before increasing LP so old
native fees cannot silently pay new principal. Unexpected offsets fail atomically.
Ordinary venue fees earned by PoPL's own LP receive the unchanged 80/10/5/5 split.
Pons creator payments are optional historical work, not a dependency of this pool.
Royalties stay separate; ZZZ-side holder fees still require reviewed ETH conversion.
The user retained the1% conversion-loss cap, gas separate, and requires a cheaper
approved conversion route. The selected approximately1.101% fee does not qualify
a full ZZZ-reward conversion at reference prices; never raise the cap to force it.

## Move funds versus exit

| Intent | Operation | Boundary |
| --- | --- | --- |
| Another fee tier with the identical actual ETH/ZZZ pair | `Migration.moveFunds(bucket,pool,minimumLiquidity,deadline)`; old `movePool` remains an alias | Atomic actual destination LP; unchanged NFT shares; one fixed 3% aggregate cap, gas separate; no external custody. |
| Send principal to your regular address | Approve request, globally pause, then `Migration.exit(id)` | Normal mode converts all attributed principal to configured ZZZ before sending; recipient custody is explicitly trusted. |
| Swap impossible / prices unavailable | Separately approve `rawExit=true`, then `exit(id)` | Transfers attributed native ETH/ZZZ under raw close minima; no 3% USD guarantee; never automatic fallback. |

ETH and WETH are distinct currencies. Atomic moves between their pools remain
unimplemented and are rejected; they need a reviewed explicit conversion boundary.
Different-pair returns through separately approved external custody remain a
manual path, with actual new-token funding and destination LP checks. Moving LP does not silently enable destination deposits or alter
routes. [Exact operator steps](GOVERNED_CUSTODY_HANDOFF.md#move-funds-without-external-custody).
The overall 3% cap is fixed, including after sealing; the narrower per-pool setting
remains configurable within its coded bounds. Raw exit is a distinct risk approval.
Native raw exit/recovery do not call WETH, but still depend on actual core/token
bindings, successful settlement and recipient transfers; there is no universal
exit guarantee through failed external dependencies.

## Remaining qualification

The fee does not automatically violate the 1% contribution budget: only the swapped
portion incurs it. Every complete input quote must still leave at least 99% as new
LP. Do not weaken the limit to pass an expensive quote. Independent ZZZ/USD pricing,
ETH/ZZZ/USDG/USDC routes, full conversion/gas economics, production inventory,
VRF, authorities, marketplace support, operating rehearsals and independent audit
remain open. Bounded post-seal VRF/buyback controls, typed v4 conversion and an
explicit ETH/WETH move boundary remain pre-seal work. Existing fork observations
retain their original WETH-accounting source scope; local native fixtures do not
qualify live services. Fresh version 2 backend/keeper pins and website integration
are required; old 8902 state/journals remain unchanged and public deployment is null.

[Native candidate evidence](../reports/native-eth-port/VERIFICATION.md) |
[Earlier selected-pool evidence](../reports/hookless-pool/VERIFICATION.md) |
[Sole Todo](../TODO.md#task-pons-qualification). Public signing stays disabled;
contracts are undeployed and production remains NOT APPROVED.
