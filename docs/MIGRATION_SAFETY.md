# Local migration budget and canonical preparation

Development candidate, 2026-10-17. Progress lives in the [central Todo](../TODO.md).
These controls do not implement cross-chain transfer of canonical NFT ownership
or reward ledgers, and do not authorize deployment or real funds.

## Aggregate budget for a local custody move

The Vault creates an immutable [migration budget helper](../src/ZZZMigrationBudget.sol).
Only that Vault can advance its checkpoints. It cannot hold or transfer tokens,
choose an executor, change a budget or call arbitrary destinations.

For `movePool` and a parked position's `resume`:

1. Capture a fresh Oracle price/decimal vector and the bucket's actual LP amounts
   plus attributed idle, before fee collection or token callbacks.
2. Harvest and allocate fees normally. Add only the exact increase in attributed
   idle from the bucket's released compounding reserve to the starting value.
3. Close when necessary, balance and deploy into the approved pool. Compare the
   final LP and attributed idle against the same captured price vector.
4. Revert the entire operation unless retained value is at least **97%** of that
   starting value. Round the floor upward. Keep the existing maximum **5% idle**
   constraint under the same captured prices, with nonzero deployed liquidity.

The 3% is one aggregate budget across the atomic operation, not a fresh allowance
for every close, swap and mint. Newly released compound is included in the
starting denominator; it cannot conceal loss. Funded owner/collective claims,
royalties, buyback reserves, other buckets and pre-existing unattributed
donations are excluded. Failed checks roll back pool reservation, LP changes,
fee settlement and helper state. Successful moves emit measured before/deployed/
idle values for operating review and cumulative cost analysis.

The floor measures **LP plus attributed idle** retained in custody. With the
existing 5% idle cap, it does not promise that 97% is deployed in the new LP.
Activation and top-ups retain their separate **99% marginal deployed-LP** rule.
Network gas is separate from both budgets.

This control covers the current supported **same ordered asset pair** and fixed
venue. It does not enforce a common execution budget over asynchronous bridging,
arbitrary conversion, ordinary keeper rebalancing or the earlier transaction
that parked principal. A parked resume starts from the then-held idle assets.
Different-pair checks remain enforced. Admitted Oracle, venue and token behavior
remain trust dependencies; a cached vector cannot prove an initially dishonest
price or a malicious venue's accounting correct. A per-operation cap also does
not bound the cumulative loss of repeated migrations.

## Reversible preparation before a canonical handoff

The [access controller](../src/ZZZAccessController.sol) accepts an exact
`PreparationNotice` only through its existing timelock, after sealing, on the
current canonical chain. The notice commits to a destination chain/controller,
deployment commitment and review hash, with a source-domain hash and increasing
nonce. This is an announcement, not proof that the successor is safe or ready.

| During preparation | Behavior |
| --- | --- |
| New mints, activation and top-ups | Blocked, including Entry cleanup callbacks |
| Rebalances, compounding, buybacks and new outbound principal | Blocked |
| Protocol module configuration, migration proposals and local pool moves/resumption | Blocked |
| Existing NFT transfers and both funded reward claims | Remain available; source is still canonical |
| Pending VRF fulfillment and ordered reveal | Remain available; no reroll or fallback is added |
| Harvest, inbox synchronization, incoming principal/rewards and finalization | Remain available under their existing guards |
| Funded reward delivery and acknowledgements | Remain available to settle outstanding obligations |
| Guardian pause and timelocked unpause | Retained; unpause does not bypass preparation |
| Timelocked parking, parking invalidation and cancellation of scheduled moves | Retained for orderly draining |

New work and ordinary configuration check their guards again after external
callbacks. A matured announcement cannot execute inside one of those operations
and let the operation finish despite the preparation restriction.

Only the timelock can cancel preparation, and cancellation must identify the
exact current notice. Old queued cancellation data cannot cancel a later notice.
No custody or canonical rights leave in this phase, so cancellation needs no
cross-chain proof. No terminal freeze, export, import or successor activation
entrypoint is exposed by these changes.

Preparation applies to this canonical controller. It does not authenticate a
stop instruction to satellites or prove that remote channels have drained.
That coordinated readiness protocol is still required before a full handoff.
Inherited timelock role administration, scheduling and cancellation keep their
existing authority rules; preparation does not freeze every governance datum.
The configured timelock delay remains immutable (`updateDelay` always reverts).

Missing return routes, failed dependencies or role changes that require new
configuration must be addressed before announcing, or after timelocked
cancellation. Preparation is not an emergency replacement mechanism.

## Keeper behavior during preparation

The keeper checks the controller's `preparationActive()` before maintenance and
again before recording/signing a new intent. It defers rebalances, compounding
and buybacks while continuing receipt recovery, harvest, funded settlements and
metadata refresh. Contracts enforce the restriction if preparation begins after
the keeper's last read. Health reports an intentional preparation state separately
from an unknown or malformed response, which fails closed.

The new keeper requires a controller implementing this getter. Updating it alone
against an older fixture/controller would stop submissions; qualify the complete
deployment together. Existing isolated staging is unchanged. See the scoped
[keeper evidence and compatibility review](../reports/canonical-preparation/keeper/README.md).

## Finality policy for the future complete handoff

The user selected **verified finality, with no multisig-only override** on
2026-10-17. Future successor activation must verify the finalized, irreversible
source retirement for the exact approved handoff and fully funded imported
state. A governance statement, timeout or provider's send receipt is insufficient.
Proof support must be qualified for the chosen destination; until then that
handoff remains unavailable. Read the [canonical migration design](CANONICAL_MIGRATION_DESIGN.md)
for cutoff capture, complete ledgers/inventory, backing and abort requirements.

The original system is not migration-capable merely because preparation exists.
The complete freeze/export/import and single-successor protocol remain a
pre-seal requirement. Post-halt recovery remains deferred.
