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
code/wiring, WETH proxy policy, admitted assets/feeds and existing strategy bounds.
No dynamic fees, custom hooks or other native tokens are admitted. WETH/ZZZ uses
ordinary hookless `configure`. Exactly one pool accepts contributions at a time.

LiquidityManager uses native ETH at the venue and WETH internally. It preserves
prefunds and clears exact allowances. Vault harvests before increasing LP so old
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
| Another fee tier or native ETH / WETH venue | `Migration.moveFunds(bucket,pool,minimumLiquidity,deadline)`; old `movePool` remains an alias | Atomic actual destination LP; unchanged NFT shares; one fixed 3% aggregate cap, gas separate; no external custody. |
| Send principal to your regular address | Approve request, globally pause, then `Migration.exit(id)` | Normal mode converts all attributed principal to configured ZZZ before sending; recipient custody is explicitly trusted. |
| Swap impossible / prices unavailable | Separately approve `rawExit=true`, then `exit(id)` | Transfers attributed WETH/ZZZ under raw close minima; no 3% USD guarantee; never automatic fallback. |

Native/WETH venues share the ordered WETH/ZZZ accounting pair. Other pairs require
external custody. Moving LP does not silently enable destination deposits or alter
routes. [Exact operator steps](GOVERNED_CUSTODY_HANDOFF.md#move-funds-without-external-custody).
The overall 3% cap is fixed, including after sealing; the narrower per-pool setting
remains configurable within its coded bounds. Raw exit is a distinct risk approval.

## Remaining qualification

The fee does not automatically violate the 1% contribution budget: only the swapped
portion incurs it. Every complete input quote must still leave at least 99% as new
LP. Do not weaken the limit to pass an expensive quote. Independent ZZZ/USD pricing,
ETH/ZZZ/USDG/USDC routes, full conversion/gas economics, production inventory,
VRF, authorities, marketplace support, operating rehearsals and independent audit
remain open. Fork prices, authority and randomness are explicitly synthetic.

[Current evidence](../reports/hookless-pool/VERIFICATION.md) |
[Sole Todo](../TODO.md#task-pons-qualification). Public signing stays disabled;
contracts are undeployed and production remains NOT APPROVED.
