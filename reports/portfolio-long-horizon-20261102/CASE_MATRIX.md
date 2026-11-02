# Main/residual lifecycle and operating case matrix

Reviewed2November2026 against main `d00201f` production sources. Two physical
positions in **one** ETH/ZZZ pool, not two separately activated pools. This is a
finite threat/lifecycle inventory; it does not claim every possible market or
execution is verified. [Execution and evidence scope](VERIFICATION.md).

Evidence labels: **N** new composed local-core campaign; **R** earlier scoped
local-core evidence at unchanged production sources; **S** inspected mechanism;
**Q** real operating/market qualification remains open. R is not a fresh rerun.
Existing local fixture bodies are in [OptionalPortfolioCore](../../test/OptionalPortfolioCore.t.sol);
the prior [LP audit](../lp-lifecycle-audit-20261102/VERIFICATION.md) records their
actual successes, failures and corrected expectations.

## What the NFT owns

Each NFT owns independently recorded shares of the logical bucket's aggregate
principal: main + residual + attributed idle/designated compound. It does not
own one physical Uniswap NFT or a personal60/40 subportfolio. Funded rewards,
royalties and buyback reserves remain separate classifications. Never add raw L
across different tick ranges as a value measure.

Activation/growth checkpoint incumbents, harvest both actual legs, freeze prices,
and swap/deploy only incoming funds into the existing main. Incumbent residual L,
IDs, centre and rebalance clock stay fixed. A swap can still reprice both legs or
change the residual's asset mix: unchanged L does not mean unchanged token
amounts or USD value. The entrant buys shares using repriced aggregate NAV, not
just the main or a historical deposit value. Earlier allocated fees remain with
incumbents; later receipts can accrue to the new activated member.

## Market and geometry states

The residual range is wholly contained in the main range at creation. Both use
the same pool's stored tick and keep their geometry until a guarded adjustment.
Therefore an active residual with an inactive main is **not a reachable normal
state** under this geometry. If price exits the main, both are outside on the
same asset side. Reference disagreement affects permission to act; it does not
change where actual swap fees are earned.

| Case | Expected handling | Evidence |
| --- | --- | --- |
| Main active, residual outside on its original side | Main may earn swap fees; the residual holds its excess asset and remains valued/harvested. No independent replacement or third leg. | S/R; N composed path |
| Price enters residual | Residual becomes mixed and may earn alongside the active main. It remains the same registered LP ID/L. | N mixed-state case |
| Price passes through residual but stays within main | Residual becomes one-sided in the opposite asset; the main remains active. No fabricated reward or automatic close on fill. | S, R physical-amount tests; economics Q |
| Price exits either main boundary | Both legs are outside on the same raw asset side. Preserve inventory and accrued fees. Hard cooldown/confirmation/execution guards still govern automatic adjustment. | N both directions |
| Price reverses back across old ranges | The same positions become active/mixed again as the stored tick crosses their bounds. Do not create more residuals just because inventory changes. | N reversals; S nested geometry |
| Same-direction trend through several adjustments | Each successful replacement closes old legs and creates one main plus at most one useful residual. Registered active IDs stay bounded; historical IDs are not additional live backing. | N multi-day cycles |
| Very narrow residual / large gap / tiny residual amount | Rounded geometry may be infeasible or too small to mint. Tiny leftovers remain attributed idle; larger infeasible placement must revert rather than silently omit backing or relax floors. | S/R; actual venue economics Q |
| Main active exactly at lower tick / downward initialized crossing | Use actual stored tick semantics; sqrt alone is insufficient. Final main-activity guards remain. | R routing boundary cases |
| Weight drifts from60/40 after trades, contributions or compounding | Expected. Governed main>=60%/residual<=40% is tested at replacement using captured post-cost valuation; it is not continuously maintained. | N/S |
| One or both independent USD feeds fail/disagree | Financial entry/maintenance fails closed as applicable. Raw ownership and funded claims remain separate; missing USD must not become zero. | N outage/recovery; R reader/callback evidence |
| Target pool and independent market disagree | Ordinary confirmation cannot treat a local-only pump/dump as sufficient. No automatic emergency bypass. | S; R confirmation/keeper evidence; live market Q |

## User actions and ordering

| Case | Expected handling | Evidence |
| --- | --- | --- |
| First activation while desired mode is enabled | Opens the initial main. No residual is forced merely by activating; optional residual creation belongs to later ordinary whole replacement. | S/R initial-entry separation |
| New activation with two existing legs | Harvest/checkpoint incumbents, deploy entrant funds into main only, issue shares of aggregate NAV, then add one collective membership. No past allocated rewards or duplicated membership. | N ETH/ZZZ Entry; R aggregate-NAV case |
| Growth with two legs | Increase main only; residual ID/L, centre and clock remain. Increase that NFT's shares by its net funded value; no extra collective membership. | N both assets; R growth/NAV |
| Contribution while mode disable is pending | Use the actual old portfolio until merge. Desired false does not hide the residual or deactivate an NFT. Financial and idle guards still apply. | S/R disabled-mode composition |
| Entry while main is outside | Separate approved entrant policy can permit it with explicit inactive-LP warning. It must still deploy at least the required marginal value; it does not recenter the pool. Both legs are then outside under nested geometry. | R initial/growth outside policy; S |
| Growth amount below effective admitted minimum | Effective floor is max(action policy, pool minimum). Reject atomically. A5USD action default cannot override a100USD pool minimum. Fresh example uses5USD pool minimum. | N rejected25USD under100USD fixture, admitted5USD campaign |
| ERC20 exact approval / native ETH | Exact ZZZ source amount is consumed and Entry/Vault approvals reset. ETH needs no ERC20 approval. Core swap/deploy/accounting is atomic; separately confirmed approval and network gas are not refunded by a later revert. | N ETH/ZZZ reviewed Entry; R approval/callback checks |
| Multiple users enter before a ready rebalance | Each call uses current shares/NAV and checkpoints old receipts. Main L changes do not invalidate stable geometry samples. Actual execution still rechecks current controls/prices. | N users-before-rebalance |
| Rebalance executes before queued contributions | Old physical IDs burn; contributions resolve the new main from the logical bucket, not a saved old main ID. Reviewed caller floors can still reject stale amounts. | N rebalance-before-users; S caller floors |
| Claim before/after another user's entry or claim | Pay only the current NFT owner's funded balance. Another holder's liabilities/reserves remain backed. Newly eligible NFTs can earn receipts generated after joining, including later entry swaps. | N partial claims and later receipts; R allocation composition |
| NFT transfer before a queued action | Write-time ownership is authoritative. Previous owner cannot use an old review to grow or claim; past unclaimed rights follow the NFT. | R transfer test; S ownership checks |
| Expired, zero, excessive, wrong-asset, wrong-owner or replayed activation request | Reject through existing owner/asset/amount/deadline/state guards. Failed call cannot create shares, mutate a residual or retain a half-completed activation. | S/R; not all permutations rerun here |
| External callback tries to join/claim/change policy mid-operation | Nonreentrant critical sections and captured contexts/final checks prevent adopting callback-mutated accounting or relaxed policy. A failing leg rolls back the whole transaction. | R actual-core failure/callback injections; upstream qualification Q |
|1000 holders share a bucket | Normal LP collect/rebuild work is bounded by physical legs, not1000 LP operations. Individual holder claims remain per NFT; terminal allocation/payout is bounded batches. | S; maximum-populated target gas/load Q |
| Two users submit from different browsers/servers | The chain serializes transactions; order can change quotes/readiness. Each actual call revalidates. Pending recovery must use the same saved transaction, not blindly resend. | N serialized core order only; RPC/browser/load/reorg operations Q |

## Management and multi-day operation

| Case | Expected handling | Evidence |
| --- | --- | --- |
| Mode off -> on | Records desired geometry; it creates no LP immediately. Next eligible guarded whole adjustment may create one residual if useful. | N multi-day cycles; R mode revision cases |
| Mode on -> off with a live residual | Keep both legs until successful atomic merge. No global pause is required for ordinary merge. Failed merge retains both legs and old rights; the earlier mode setter stays mined/pending. | N repeated merges; R failure rollback |
| Enable -> disable -> enable before execution | Monotonic revisions do not revive old observations/reviews even when final bool matches its old value. | R current lifecycle case |
| Desired on but residual ID0 | Can be valid applied state when the natural main meets the floor. Do not force40%, invent another leg or confuse desired policy with physical state. | R current lifecycle case; S |
| Configure width/gap/main floor | Future guarded adjustment applies reviewed geometry after cooldown. No direct mutation of existing ticks. Captured revisions/physical identity block restore-to-revive reviews. | S/R governed geometry/callback cases |
| Hourly harvesting over several days | Collect both actual IDs and split combined actual ETH/ZZZ receipts80/10/5/5 once, with raw-unit dust carried. Harvest does not swap/compound/burn or pay all holders. | N18 spaced harvests plus internal receipts; R exact allocation |
| Standalone compounding with two legs | Reinvest attributed idle/designated reserves into existing main; residual L and NFT shares do not change. Keeper waits below adjustment threshold, in range and with no pending geometry. | N repeated real Compounder execution; S automation policy |
| Near-trigger, outside or manual change pending | Keeper waits rather than using compound swaps as a hidden rebalance bypass; harvest remains separately scheduled when allowed. Hard12hours can intentionally leave inactive inventory. | S/R keeper policy; real cadence Q |
| Accumulated unused assets / keeper outage | Retain attributed idle and compound backing. New entrants cannot subsidize old idle or bypass deployed-LP floors. Resume/reconcile current chain state; use guarded compound/adjustment/parking as appropriate. | N idle/reserve reconciliation; R recovery evidence; off-host outage Q |
| Residual-only paused close | Harvest both, close only residual to same-bucket Vault idle. Main/shares/clock persist. Desired mode must be disabled separately to prevent future residuals; unpause is separate. | R exact close/replay/policy/owner/callback tests |
| Park and resume / same-pair move | Close both and retain classified assets. Resume/move validates destination and current policy; never leave a live source residual behind. | R both-leg parking/movement; actual destination Q |
| Emergency one-main consolidation | Paused governance exact manifest can deliberately bypass selected financial gates. Produces one main at the range-required ratio, not necessarily50/50USD. It does not silently disable desired hybrid mode. | R forced controls; S accepted governance trust |
| Terminal holder return | Close both without required swaps, preserve reward/buyback backing, allocate principal by NFT shares and pay current owners in bounded isolated batches. No LP reopening; old claims/transfers/future royalties remain. | R collective-exit composed case; maximum batches/recipient behavior Q |
| Canonical same-chain replacement | Parked lifecycle requires zero registered live residuals and exact ledger/backing/runtime admission. Compatible record wire alone cannot upgrade deployed code. No integrated bridge. | S/R separate canonical evidence; live cutover Q |
| One leg mint/collect/burn fails, or prices/controls change in a callback | Whole guarded call reverts; do not publish half a portfolio or forget a liability. Separately mined earlier settings/pause calls are not rolled back. | R second-mint/burn/callback tests; S exact contexts |
| Reorg, process crash, disk/nonce/RPC fault | Recover pending receipts before new work; retain exact release/profile/config/journal and observe confirmed chain. Never reconstruct a missing residual as zero or relabel an old deployment. | S/R runbooks/backend; sustained real service qualification Q |

## Constraints to retain in the long-term plan

1. Optional residual inventory reduces immediate balancing swaps in some states;
   it does not eliminate impermanent loss, adverse selection, market risk or MEV.
   Persistent sampled evidence is not uninterrupted price history.
2. Repeated3% permitted operations can compound losses; the user retained a
   per-operation cap rather than a cumulative cap. Track realized cost and
   trading fees separately. No profitable60/40 optimum has been demonstrated.
3. Small5USD growth and frequent hourly work still need real gas/economics
   qualification. Exact object sizes and synthetic-feed tests do not qualify a
   live chain/provider/venue or100 concurrent website users.
4. Idle, main-floor, total-loss, additional-loss, price and caller guards can
   legitimately block maintenance. Diagnose the exact blocker; do not silently
   widen policy or automate the manual emergency path.
5. Source6 consumers/services are not the older served sites/Anvil deployments.
   Preserve source/runtime pins and old journals; publication alone changes none
   of them. Independent audit and actual release gates remain in the sole Todo.
