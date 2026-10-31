# Optional two-position LP: implementation plan

Authorized 30 October 2026. This is a fresh source candidate, not a deployment or
an instruction to modify existing services, Anvil state, wallets or journals.
The [sole Todo](../TODO.md#task-passive-inventory) tracks delivery. The earlier
[research](PASSIVE_INVENTORY_PLAN.md) remains evidence, not implemented behavior.

## Target and fixed requirements

- Default single main position. Governance may enable an optional main plus one
  residual for an admitted native ETH/fixed-ZZZ pool. No automatic attack detector.
- Ordinary adjustment at 85% of the actual centre-to-boundary price distance,
  expressed as ZZZ in ETH. Physical and independent-reference prices must agree
  on the same threshold side. Preserve healthy prices and existing financial guards.
- Ten-minute sampled confirmation, four-minute source checks, maximum five-minute
  confirmed gap, then one durable random 60-300-second delay. Recheck through the
  delay and before submission. Preserve the hard initial twelve-hour interval.
- Manual width/mode changes apply at an eligible guarded adjustment after cooldown;
  changing desired policy does not immediately trade or move principal.
- Hybrid mode deploys at least 60% of post-cost attributed principal in the main,
  at most 40% in one residual; do not force a 40% allocation. Swap only the amount
  needed to meet the floor, using bounded reviewed-venue quotes and existing caps.
- The 60/40 test applies after replacement, not continuously and not to entrants.
  Both positions may subsequently become mixed or change value as markets move.
- Disabling hybrid mode records a desired single-position state. Until a safe
  atomic merge succeeds, continue accounting for, valuing and harvesting both.
- At most two registered physical LP NFTs per bucket, both owned by Vault. No
  third position, external custodian, new asset or public signing permission.
- Hourly harvesting remains independent. Claims and funded royalties retain
  existing rights. Preserve 80/10/5/5, entrant-only budgets and independent shares.

## Scope decisions

Manual widths already remain configurable within the current Registry bounds;
this task does not increase the 50% maximum or change existing loss limits.
The latest user decision is HALF the corresponding side, default5000bps of
that side; governance may configure1–10000bps. For main50–150 around100, the
residual spans approximately75–100 or100–125, one full aligned tick-spacing
away from spot. The earlier full-side initial choice was superseded before completion.
No fully filled residual is automatically closed or replaced on its own: it
remains part of the bounded portfolio until the next whole adjustment.

## Architecture and compatibility

1. Preserve the eight-word Position wire record and its actual main LP ID. Expose
   auxiliary identity explicitly, without adding raw liquidity across ranges.
   Vault owns both NFTs; a fixed Manager association rejects duplicates/orphans.
2. Introduce explicit fresh accounting5 / portfolio1 / maintenance3 /
   confirmation3 capabilities. Historical accounting4 and older readers, profiles
   and pending records retain their meanings. Current deployed code is unchanged.
3. Keep physical `amounts(actualId)` separate from aggregate portfolio valuation.
   NAV/share pricing, metadata and all read services use both authenticated legs.
4. A fixed noncustodial policy helper owns reviewed geometry/trigger/mode policy.
   Mode/geometry revisions and physical identity invalidate samples, jitter and
   unsigned reviews; healthy price rounds or normal main contributions do not
   reset the LP's centre/cooldown. Submitted transactions always recover first.
5. Separate creation-size-heavy components rather than relaxing EIP-170/EIP-3860,
   optimizer settings or authority. Measure every affected module. No delegatecall
   or generic executor is introduced. Constructor/helper binding changes require
   deployment inventory and source-bound readers to be updated explicitly.

## Work packages and affected components

| Package | Target | Required integration |
|---|---|---|
| Policy and confirmation | Strategy, Confirmation, new fixed PortfolioPolicy | Exact inverse-price math, threshold sides, sampled condition versus cooldown readiness, mode pending, policy revisions, full physical identity. |
| Execution | LiquidityManager, LPBalancer and typed helpers | Minimum-to-main-floor sizing, exact one-sided mint, at most two IDs, per-NFT approval, actual balances, core quotes, atomic all-leg collection/close. |
| Accounting | Vault, MigrationBudget, ContributionPricing, metadata | Aggregate NAV and incumbent checkpoints; entrant increases main only; separate reserves; actual post-cost utilization proof without weakening loss/idle limits. |
| Recovery | Migration, canonical companions, emergency manifests | Both legs close for parking/pool move/holder return; full identity in manifests; no residual survives parked export; same-chain V5 wire only if these conditions are proved. |
| Keeper | monitor, confirmation, compound policy, health and operation report | Fresh profile, cooldown observations, 600/300 sampled evidence, durable 60-300 jitter, reset/restart/pending recovery, desired single mode with live residual. |
| Readers and preparation | zzz_ops, frontend API, observers/preflight/config | Exact fresh capabilities and aggregate physical observations; historical codecs stay separate; complete unsigned reviews include new policy/portfolio identity. |
| Documentation | Operator, callable reference, features, roadmap, Todo, context/handoff | Exact inputs/outputs/permissions, enable/disable/merge steps, rollback and known qualification limits. |

## Verification and completion

Freeze original dirty-file hashes and source identities before edits. Add focused
checks before relying on new behavior: both trigger directions/orientations and
rounded boundaries; cooldown and sampled gaps; mode/range changes during jitter
and callbacks; trends/reversals/fill/unfill; limited inventory and failed quotes;
60% floor versus 40% ceiling versus 5% idle versus total loss; exact fee conservation;
contributions/claims/transfers; failure of the second mint/collect/burn; all-leg
parking/movement/emergency/holder return/canonical export; legacy profile rejection.

Compile at the unchanged normal profile and satisfy every runtime/initcode gate.
Run affected actual-core Solidity and keeper/API checks; preserve failures and
source-stage scope. Reuse unchanged evidence only at exact pins. Research models
are not contract execution. Actual feeds/routes/gas/host/marketplace qualification
and independent audit remain open. No service/site rollout or public transaction
is authorized by this implementation task.

The plan was recorded before implementation. The local source now includes
the policy, execution, accounting, recovery, keeper, read/unsigned and inventory
integrations above. [Current verification](../reports/optional-portfolio-20261030/VERIFICATION.md)
retains failures and exact source-stage scope. No service or website was rolled
out. Target-chain economics/gas, real dependencies, current website acceptance
and independent audit remain release work in the sole Todo.
