# LP allocation, claims and reserve execution review

Scope: current native accounting3/fee intake1, the fixed80/10/5/5 split, equal
activated membership and keeper scheduling. This is an internal source-scoped
review, not an independent audit or production approval. No production Solidity,
rate, permission, custody or claim behavior changed.

## What happens and when

1. The pool earns fees while the position participates. Actual collection through
   Vault funds FeeController; it allocates80% to per-bucket share-indexed holder
   rewards,10% to the collection-wide equal-eligible index and5%/5% to classified
   compound/buyback reserves. There is no per-minute distribution or holder loop.
2. Collective membership is the eligible count at receipt processing. Dormant
   NFTs have none; activation grants one and top-ups do not increase it. The
   contribution bucket is harvested/checkpointed before newcomers join. A separate
   historical bucket's unharvested fees retain their documented receipt-time policy.
3. A claim settles only that NFT's indices/fractions, pays the authenticated current
   owner and reduces its liability. Other NFTs, membership and reserves do not
   change. Repeated claims cannot replay paid balances. Transfers carry only the
   unclaimed remainder to the new owner.
4. Compounding uses a separate keeper action and can also occur along guarded
   contribution/rebalance paths. Buyback is a separate keeper action, spending
   only its classified reserve and verifying an actual supply-reducing ZZZ burn.
   Neither depends on an NFT claim; failed execution reverts its own reserve use.

Twenty raw units split16/2/1/1. Smaller receipt dust carries, then at entry/movement
barriers goes to incumbent individual shares (at most19raw units per settlement).
Per-NFT fractions survive claims; global index division dust stays reserved. Do
not promise that every last raw unit is immediately claimable or reinvested.

## Finding fixed: reserve execution starvation

The keeper previously tried buybacks only after all eligible maintenance and
metadata work. Continuous rebalances could prevent any buyback; a perpetually
funded first currency could also monopolize the list. This was a liveness defect:
the reserve stayed backed, but allocation alone did not imply a timely burn.
Three regressions fail against the pinned original monitor, with no fixture errors.

The fix alternates buyback priority with reached maintenance opportunities and
rotates currencies. Existing conversion priority, pending-first recovery and the
normal simulation/gas/fee/nonce path remain. At most32 unique configured input
currencies and optional validated cursor/phase fields keep work bounded; old
journals default without reset. Failed pre-submission currency reads/simulation
defer that task; any error after a pending intent exists stops further work.
Empty buyback configuration does not introduce scheduling state or reorder work.
Exact bytes32 validation allows zero for the unused pool field in direct ZZZ
burns; route-dependent inputs still require the existing contract simulation.

This provides opportunities, not a wall-clock guarantee. A pending receipt,
pause/preparation, unsafe trade, gas budget, inadequate reserve or failed burn
can still defer execution. The blocked example has standalone compounding off,
an empty buyback list and no live deployment approval; no installed service was
changed. Actual operating economics/latency/monitoring still require qualification.

## Verification and remaining limits

[Verification](VERIFICATION.md) records two new accounting methods (including
1,000 randomized schedules), the final affected keeper suite and exact input
bindings. No new accounting defect was found within this scope. Existing real-v4
harvest/rebalance, failed payout, conversion and buyback execution evidence is
reused only at its original source scope; these lightweight accounting fixtures
do not replace target-token, route, feed, gas or independent qualification.

Operator guidance now separates earned/unharvested, indexed/claimable, paid,
reserved and executed-burn values. Safe operation keeps the four jobs separate,
uses reviewed economic thresholds/gas budgets and watches backlog/error/receipt
age instead of forcing swaps inside holder claims.
