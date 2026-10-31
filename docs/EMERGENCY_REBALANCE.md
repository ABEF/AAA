# Manual emergency LP recovery

Fresh accounting6 source candidate; production NOT APPROVED. Current normal
gates, scoped offline checks and local actual-v4-core integration pass within
their [source scope](../reports/residual-operations-20261031/VERIFICATION.md);
live operation/dependency qualification remains open. No deployment, signing or service
restart is supplied by this procedure. Ordinary upkeep uses the
[independent confirmation policy](LP_EXECUTION_POLICY.md#requested-rebalance-confirmation-buffer).

## Authority and risk

Only the current governance wallet may call `Migration.emergencyRebalance(request)`.
The system must be sealed, globally paused, outside canonical preparation/import/
retirement and before terminal collective LP exit. There is no keeper scheduler,
holder action, user-transaction API or automatic retry fallback for this function.

The operator explicitly selects which economic checks to retain for this single
transaction. **Disabling financial checks permits a bad trade that can lose almost
all principal.** Approved venues and exact bookkeeping do not stop governance
from trading against a related party at an unfavorable price. Manual execution
and pause do not protect against a compromised governance key or public ordering.
This authority is an explicit governance trust expansion, not protection against
malicious governance. Do not describe the ordinary loss caps as unconditional.

The function cannot change the deployment ZZZ, send principal to another address,
use arbitrary calldata, rewrite NFT shares, spend holder reward/buyback reserves,
revive terminally exited LP or replace canonical ownership. Exact received assets,
LP ownership, typed venue identity, approvals, deadline, accounting and lifecycle
barriers remain mandatory. A broken token/core or nonexistent executable liquidity
can still prevent recovery.

Ordinary reference protection and automatic keeper width policies cannot be
enabled together. Deliberate governance widths remain supported. An emergency
uses explicit ticks and is independent of automatic width selection. When bit16
is retained, the stable confirmation policy and raw observations are captured
across callbacks even if bit4 financial checks are disabled.

## Request and retained-check mask

| Input | Meaning |
| --- | --- |
| `bucket` | Shared Vault custody bucket, not an individual NFT ID. |
| `custodyHash` | Exact current `Migration.emergencyCustodyHash(bucket)`: chain, Vault, bucket, full Position, total shares and the liquidity-sensitive fingerprint of both physical legs. A different LP, park, move, idle/share/deposit change requires a new review. Market price changes alone need separate execution protection. |
| `checks` | Sum of retained bits below; integers 0-31 only. It is a per-call selection, not a persistent keeper setting. |
| `lower`, `upper` | Explicit physical v4 ticks in raw pool-key order, within TickMath bounds and divisible by the admitted pool's tick spacing. These are not percentage values or inverted display prices. |
| `swapPool` | Already admitted static hookless native ETH/fixed-ZZZ venue, or zero if no swap. This manual path does not run the automatic best-venue solver. |
| `zeroForOne` | True sells native ETH for ZZZ; false sells ZZZ for ETH, under the admitted native-first ordering. |
| `amountIn` | Exact raw input, bounded by actual attributed idle after closing/releasing compound. Zero means no swap; it requires zero `swapPool` and `minimumOut`. |
| `minimumOut` | Positive raw output floor if swapping. Match actual token decimals. An unrealistically tiny floor accepts extraction; the fixture value1 is not a production recommendation. |
| `minimumLiquidity` | Positive raw Uniswap liquidity floor, derived from complete post-close/swap/redeployment simulation. Not USD or token amounts. |
| `deadline` | Unix seconds; inclusion must satisfy `now <= deadline <= now+600`. |
| `reviewHash` | Nonzero commitment to the exact reviewed operation/evidence. It records a review reference; it cannot prove review quality. |

| Retain bit | Checks kept |
| --- | --- |
| `1` | Raw ordinary 85%-threshold-or-deliberate-geometry eligibility and hard cooldown. It also retains dependencies of that raw Strategy read. |
| `2` | Fresh independent prices and spot/reference agreement before/after execution. |
| `4` | Captured aggregate maintenance retention, venue/fee-adjusted output floors and idle ceilings. Valuing these limits still requires healthy USD prices even if bit2 is off. |
| `8` | Pool `operationsEnabled` admission for deployment/swapping. |
| `16` | Existing sampled confirmation, still fresh at inclusion. Pause does not create observations or stop their expiry. An absent/stale/stopped window rejects if this bit is selected. The established deliberate-range exception remains. |

For example, retaining `2+4+8` keeps financial/venue checks while bypassing timing
and sampled-trigger requirements. Zero explicitly disables all five optional
groups; it does not disable the structural requirements above. Never retry with
fewer checks automatically. Deliberately lowering protection needs a fresh human
review and exact simulation.

## Consolidating to one position

This function already closes both positions and always creates just one main.
Set `PortfolioPolicy.setMode(pool,false,reviewHash)` first to keep later ordinary
adjustments single; emergency execution does not silently change desired mode.
Use the actual concentrated range's required token ratio, not a hardcoded50/50USD.
Closing only the residual without replacing the main is the separate paused
governance [residual-close procedure](OPERATOR_MANUAL.md#portfolio-management-controls).

## Operator procedure

1. Verify the chain, sealed deployment, current governance and exact source/ABI/
   runtime profile: accounting6/custody4, confirmation3 plus emergency capability2. Coordinate/stop the
   automated signer and reconcile every pending hash before manual work. Stopping
   a host does not cancel a broadcast transaction. Preserve journals.
2. Governance pauses through `Access.setPaused(true)`. Read actual custody, shares,
   raw balances, fee reserves, active/parked status and `emergencyCustodyHash`.
   The function accepts Active or Parked custody; terminal Exited is excluded.
3. Choose explicit target ticks and one reviewed native ETH/ZZZ swap venue/amount,
   or no swap. Evaluate depth **after withdrawing our old LP**, both trading fees
   and impact, raw output/deployment floors and separate network gas. A forced
   request cannot rely on the oracle-based automatic planner when that oracle is
   deliberately bypassed. A raw range outside the actual price need not earn fees.
4. Select retained checks, record why each disabled check is necessary, and
   simulate exact governance sender, Migration destination, zero transaction
   value and full request at fresh confirmed state. Simulate the entire operation,
   including final harvest, actual close of both physical legs, optional swap and one emergency target mint. This emergency path does not create a residual. Raw minimums
   remain binding even if other financial guards are disabled.
5. Governance signs once. Its wallet/Safe execution pays network gas; no NFT
   holder action or keeper grant is required. A revert rolls back closing, fee
   allocation, swap, approvals, temporary emergency context and new LP atomically;
   transaction gas remains spent. Recover an ambiguous result by the same hash.
6. Confirm the canonical successful receipt and `EmergencyRebalanced` commitment/
   mask, plus Vault `Rebalanced`. Check actual new main ownership/ticks/liquidity, absence of an orphaned residual,
   actual token deltas, unchanged per-NFT/total shares and contributions, preserved
   earned rewards/buyback reserves, accounted idle/compound and cleared temporary
   emergency state. Check actual range activity; a mint alone does not prove it.
7. The protocol remains paused. Repair/qualify prices, venues and ordinary policy
   before unpausing. A raw emergency range that differs from configured ticks or
   desired/applied portfolio geometry can
   leave `rangeUpdatePending` for the next ordinary maintenance cycle. Successful
   replacement anchors a new rebalance clock; obsolete observations cannot qualify
   its new physical LP identity. A later deliberate ordinary geometry repair retains
   price/tick/cooldown/financial guards but need not interpolate an old centre outside
   the emergency bounds. No persistent bypass setting is left behind.
8. Resume services only with matching source/profile/runtime/config health,
   confirmed resets and reconciled pending/nonce/spend records. Using the same
   signer outside its journal needs explicit reconciliation; restart alone is
   insufficient. No new wallet or operator committee is implied.

This is not [collective holder exit](HOLDER_COLLECTIVE_EXIT.md): principal stays
in Vault-managed LP. It is also separate from normal manual `Vault.rebalance`,
which retains every ordinary on-chain guard and requires a keeper grant.
