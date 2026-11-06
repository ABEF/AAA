# Moving-market preparation and same-main consolidation

6November2026; baseline main7cc0f55. Production NOT APPROVED.
[Executed scope](PROMPT.md). Production code and interface are unchanged.

## Result

No new ordinary tick-race principal-loss defect was confirmed. The main's
lower/upper bounds are fixed for its physical LP ID; swaps move current price,
composition and fees. Activation/growth changes actual L and shares without
recentering. Full replacement creates another main identity. Same-main
consolidation cannot apply a new range to the old position.

The original operator recipe omitted an explicit confirmed-pause/coherent-block
preparation step and could be read as if custodyHash locked price or every
configuration setting. The maintained [manual](../../docs/OPERATOR_MANUAL.md#fixed-bounds-moving-markets-and-fresh-reviews)
now explains the distinction, repeated-operation discovery, current-state full
simulation and recovery. No new live reader/planner or signing capability is
implied: the offline review helper only validates/hashes supplied evidence.

## Source trace and cases

| Change after preparation | Current behavior / boundary |
| --- | --- |
| External trade changes current tick inside main | Bounds and L identity remain. Actual recovered composition, route and deployment use execution state, subject to current guards and positive caller floors. |
| External trade crosses either main boundary | Guarded capture/postcondition requires stored tick in `[lower,upper)`; failure reverts the entire management call. The custody hash can remain unchanged because spot is not custody identity. |
| Own balancing trade pushes main inactive | Final physical proof rejects; bounded solver may miss an alternative feasible route. Safe failure is not always-feasible routing. |
| Contribution executes before pause | L/shares/idle/custody can change; old identity rejects. Snapshot after confirmed pause and review again. |
| Contribution attempts after pause | Ordinary live gate rejects. External trading continues. There is no transaction interleaving inside one complete call. |
| Full rebalance/move changes main | Use fresh main ID/bounds/hash; old request is not authority to increase a replacement under old identity. Raw ticks on a burned/nonexistent ID may return0,0; authenticate current Vault main custody first. |
| Raw close, earlier consolidation, parking or recovery | Nonce/epoch/portfolio identity changes; old request is not replayable. |
| NFT transfer or healthy funded reward claim | Their independent rights continue. Current ownership and earned balances do not grant principal-management authority or redefine position bounds. |
| Governance settings change before execution | Not every setting is in custodyHash. Explicit fresh review/simulation is required; current policies are captured/rechecked during execution. No permissionless setting-change path was found. |
| Oracle/RPC failure, expired deadline or impossible floor | Fail closed; refresh/recover known pending transaction, do not blindly submit duplicates or auto-enable forced bypass. |
| Callback changes sensitive state | Existing authorization, exact balance/ownership/L/context/nonce/control and final checks protect the atomic boundary; earlier scoped callback evidence is retained, not rerun here. |
| Price moves after successful consolidation | Main bounds remain fixed; future price may leave range. Normal maintenance scheduling resumes after explicit unpause. This operation cannot promise continuous activity. |
| Weeks/months and repeated optional-mode cycles | Discover current canonical identity each time; preserve receipts/journals and bounded modes. No accumulating third residual or current60/40 guarantee is introduced. |

Relevant source: Migration.consolidateResidual; CustodyValidation
captureConsolidation/verifyConsolidation/_consolidation; Vault._reinvest/_redeploy;
Manager.balance/increase/executionPortfolioFingerprint; position child's
_mintOrIncrease; Budget checkpoint and captured maintenance marks. Actual
Manager/position child/core/periphery APIs distinguish immutable range metadata
from slot0 and actual principal. Final source pins are in the verification record.

## Scope and remaining risks

The new tests supplement the earlier20-selected campaign; they are not another
full suite and their counts must not be summed with overlapping evidence.
Mock correlated feeds in local core tests are not independent market/oracle
qualification. Simulated serial order/virtual time is not months of uptime,
maximum-state gas or attack immunity. No source/runtime/capability/profile bump
or new production artifact is required because only tests/docs change.

Actual dual feeds/routes/VRF, authorities/OpenSea, provider canonical reads,
constructor/maximum workload gas, operating/recovery rehearsals, fresh service/site
adoption and independent audit/remediation remain open. Force is deliberate
governance economic risk, never ordinary fallback. Existing sites, services,
Anvil state, journals, signer and paused heartbeat are unchanged.
