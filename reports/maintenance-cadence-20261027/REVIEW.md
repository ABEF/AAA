# Coordinated maintenance: internal review

Scope: fresh undeployed accounting4 Budget companion and matching keeper, not a
deployment, service rollout, external MEV guarantee or independent audit.

## Finding and change

Rebalance used Position.lastRebalance; standalone compound used an independent
lastCompound clock with a first-use exemption. An eligible compound could follow
a physical LP replacement immediately. A symmetric shared lock would introduce
a different problem: a keeper could compound first to postpone needed rebalance.

The candidate instead uses asymmetric priority:

- Every standalone compound requires the current pool interval after
  max(lastCompound,lastRebalance). This includes no-swap/idle work and the first
  compound after activation. Successful activation, pool move/resume and ordinary
  rebalance already stamp physical LP creation; no new timestamp storage is added.
- Compound yields to a currently eligible rebalance or already-available reviewed
  adaptive range selection, including before that selection is applied.
- Rebalance never reads lastCompound. Newly eligible price/range maintenance may
  follow compound immediately; this is intentional priority, not a universal
  minimum gap between all swaps. No24-hour default is selected.
- Harvest, claims and user contributions do not acquire a new cooldown. Internal
  reserve reinvestment during those guarded contribution/rebalance paths remains.

Budget checks occur before harvest/reserve release/clock mutation. Typed view
calls cannot mutate policy during these checks. All later effects and timestamps
revert on failure. Existing caller minima, snapshot loss/idle checks, custody,
fees, 80/10/5/5 rights, permissions and governance interval boundaries remain.

The keeper authenticates helper code/pins, Vault binding and capability2 for
fresh accounting4 due compound. It uses the authoritative compoundReady boolean,
not a local journal approximation. Local interval is an additional delay only.
Historical1/2/3 scheduling/V1 reads and journals remain intact. Guarded unavailable
maintenance reads still permit an independently due guarded harvest; malformed
ABI remains an error rather than guessed eligibility. Pending recovery comes first.

## Reviewed limitations and operating impact

- compoundReady is cadence/strategy eligibility, not lifecycle/authority or an
  execution guarantee. Actual Vault calls still enforce all execution modifiers.
- A live adaptive policy with its range job disabled can defer compound until
  the intended policy/job configuration is resolved. Do not bypass the guard.
- The rule conservatively defers no-swap compounds too. A precise swap-only
  exemption would require scoped execution-phase design; existingRange alone
  is insufficient because contributions use that path too.
- Local lastCompound is operating state and is not a migrated economic ledger.
  Canonical imports preserve Position.lastRebalance; actual cutover/configuration
  and later interval choices still need release review.
- Independent real prices, slippage/depth economics and transaction ordering
  remain essential. No profitable attack was established or disproved by this
  timing fix; the existing per-operation loss policy is not a cumulative budget.
- Failed sends consume gas; RPC/keeper outages delay work. No installed service,
  journal, old Anvil deployment, website or signing policy was changed.

See [verification](VERIFICATION.md) and
[operator procedure](../../docs/OPERATOR_MANUAL.md#coordinate-compounding-with-rebalancing).
