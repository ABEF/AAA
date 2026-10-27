# Keeper and outside-actor exposure: scoped review

Base source: main1f25b7e. Fresh undeployed accounting4/custody3/compound2 candidate;
production NOT APPROVED. This review advances the two manipulation tasks without
claiming no profitable attack or qualifying real feeds, depth, ordering or services.

## Implemented findings

| Finding | Evidence and correction | Limit |
| --- | --- | --- |
| A paid revert could immediately appear healthy | A canonical reverted inert-RPC receipt charged205wei, cleared pending and set the existing action cooldown, yet run_cycle returned dry_run/healthy with no restriction marker. Health now reports confirmed_reverts plus active cooldown count/earliest retry, including after restart or unrelated success. | Synthetic receipt cost is not a Robinhood gas estimate. No journal schema, gas accounting, nonce, retry policy or global signing/backoff change. |
| Maintenance/buyback authority was only checked before callbacks | Rebalance, the original-keeper Compounder coordinator and Buyback now recheck keeper authorization/pause after external work, matching the existing reward converters' completion policy. | Defense in depth for privileged/dependency callbacks, not a demonstrated ordinary external theft or price-manipulation attack. |

The new contract checks are local to three existing functions; no global modifier
change, new callable API, role, custody path or recipient was introduced. A rejected
completion reverts all effects, including the callback's pause/revocation. A real
operator pause/revocation should still be its own normal governance/guardian
transaction. This does not let one transaction interrupt another atomic transaction.

The health checker requires matching writer fields. Active paid-revert cooldowns
remain observable while other eligible work can proceed. Expiry only permits a
retry; it is not successful execution or market repair. Pending/ambiguous and
canonical-lock status precedence remains, with markers still present. Unknown
clock/marker data cannot assert health. No saved state is edited to make it pass.

## Current exposure map

Source boundaries: [Strategy](../../src/ZZZStrategy.sol),
[LiquidityManager](../../src/ZZZLiquidityManager.sol), [Vault](../../src/ZZZVault.sol),
[Buyback](../../src/ZZZBuyback.sol),
[reward conversion](../../src/base/ZZZRewardConverter.sol) and
[keeper health checker](../../keeper/ops.py). These are implementation references,
not independent economic approval.

| Actor/path | Enforced boundary | Remaining review |
| --- | --- | --- |
| Unprivileged direct maintenance calls | Keeper/module authorization, fixed recipients, atomic accounting and lifecycle checks. | This prevents direct authority misuse, not an outside trader influencing the market. |
| Malicious keeper timing | Deterministic strategy sizing, independent-reference trigger, compound2 priority/cadence, execution minima and captured value checks. | Keeper can trade through other wallets and choose eligible execution time; permitted losses can still be economically exploitable. |
| Rebalance balancing swaps | The old LP closes before the new plan; spot/output checks and the aggregate default3% cap remain. | Measure depth after our LP is removed, including both bounded swaps and external liquidity withdrawal/addition. Pre-close TVL is not available execution depth. |
| Buyback | Fixed-ZZZ reserve only, upper-price per-call USD ceiling, admitted pool/output bounds and verified supply-reducing burn. | Keeper still chooses amount, admitted pool and timing. Quantify execution slack before changing floors, adding API or imposing new rate/cumulative limits. |
| Earned-reward conversion | Captured conversion cap, exact receipts and per-NFT source/native entitlements. | Route admission is not feasibility. Selected pool LP fee1.002% already exceeds the default1% cap at reference prices, before protocol fee/impact; require a cheaper qualified route or an explicit policy decision. |
| Outside trading/order flow | Oracle references, spot/output/loss guards; Robinhood uses sequencer-arrival ordering without an ordinary public pending mempool. | Predictive positioning, provider leakage, sequencer trust, backrunning/JIT and execution inside tolerances remain. A private-labelled auction can disclose early hints. |
| Price providers | Two reviewed sources/freshness/agreement and conservative bounds in code. | Real independent ETH/ZZZ pairs remain unqualified; two wrappers of one manipulable source are not independence. |

Normal external LP fee income or arbitrage alone is not proof of a protocol
exploit. An economic witness must compare protocol/attacker raw assets and gas/
trading costs against a matched baseline, with exact price/feed/state assumptions.

The delegated economic-attack simulation was blocked by a platform security
screen. No exploit/profitability simulation or fresh mainnet-fork campaign was
completed in this scope. Defensive callback/receipt checks are not relabelled as
that evidence. The corresponding Todo acceptance criteria remain open.

## Preserved decisions and boundaries

- Contribution2%, conversion1%, maintenance3% defaults; governed ceilings10%;
  per-pool swap limits and3% source agreement remain distinct and unchanged.
- No24-hour default, new cumulative-loss budget or automatic cap relaxation.
- Hourly harvesting remains independent; fixed80/10/5/5 and rarity royalties,
  current-owner rights and collective principal return remain unchanged.
- No public signing, contract deployment, server/service/Anvil/journal/website
  rollout or protected-submission provider activation.

[Verification](VERIFICATION.md), [operator procedure](../../docs/OPERATOR_MANUAL.md),
[keeper recovery](../../docs/KEEPER_RECOVERY.md),
[keeper task](../../TODO.md#task-security-keeper-manipulation) and
[outside-actor task](../../TODO.md#task-security-external-manipulation).
