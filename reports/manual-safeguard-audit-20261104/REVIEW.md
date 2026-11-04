# Manual operator recovery and safeguard audit

November4,2026; source baseline main0b14aca. Internal review of two objectives:
operator force/recovery reachability and normal safeguard composition. Source
candidate only; **production NOT APPROVED**.

## Prompt improvements and boundaries

The [twice-reviewed scope](AUDIT_SCOPE.md) expands “force” into concrete Active,
Parked, residual-only, whole merge, same-pair movement, maintenance, terminal
return and canonical lifecycle cases. It distinguishes optional market/timing
policy from mandatory custody/accounting and impossible external failures.
“Nothing can block” cannot hold for a frozen token/core, insufficient funds/gas,
invalid ticks or terminal retirement. Normal keeper permission is not emergency
governance authority. The [full matrix](SAFEGUARD_MATRIX.md) records dependencies,
outputs and reverse/restart boundaries rather than removing repeated checks
merely because they look similar.

## Implemented corrections

1. **Hidden emergency cooldown coupling.** Retaining sampled-confirmation bit16
   also called Strategy.needsRebalance and inherited separately selectable bit1
   cooldown/raw eligibility. Emergency sample evaluation now omits that extra
   gate. Budget still enforces bit1 when selected; ordinary readiness retains
   cooldown. Samples still need fresh matching condition/reference/control data.
   No observation is created or extended while paused.
2. **Raw-close optional floors.** Parking validation required at least one
   positive token-side output minimum, including residual close. Market movement
   can change the LP wholly to the other asset without changing IDs/ticks/L.
   Paused governance may now explicitly use both raw floors0. Positive submitted
   floors, actual current-core principal proof, receipt deltas, exact custody,
   nonce/epoch, shares, deadline, authority and lifecycle remain mandatory.
3. **Callback test repair.** An existing policy-mutation regression still targeted
   the old Manager as pool-payment recipient. The actual recipient is its typed
   LP child. The corrected test requires the callback, verifies full rollback of
   fee/principal/policy changes, then succeeds with the callback removed. No
   contract guard was removed to accommodate it.

## Practical manual routes

- Force replacement: pause; governance submits a fresh exact
  `Migration.emergencyRebalance(request)` with the deliberately selected retained
  mask. `checks=0` bypasses optional clock/window/price/loss/idle/operations policy.
- Close both temporarily: paused `Migration.park`; explicit both-zero raw floors
  can accept actual returned composition. Principal stays attributed in Vault.
- LP again despite optional policy faults: stay paused; capture a NEW Parked
  custody hash and use emergency replacement into the current pool.
- Close residual: paused `Migration.closeResidual`; main/shares/clock and desired
  mode remain. Set modefalse first to stay single after future adjustments.
- Ordinary manual Vault.rebalance, resume and moveFunds remain guarded. Emergency
  does not admit or force a different destination pool. Terminal return and
  canonical ownership locks remain irreversible/authenticated.

The sending governance wallet pays gas. No principal recipient, sweep, new role,
holder withdrawal, automated emergency fallback or deployment was added.
See [exact operator inputs](../../docs/OPERATOR_MANUAL.md#force-close-and-redeploy-choose-the-correct-call).

## Safeguard composition conclusion

Normal protections are unchanged. Source agreement, spot deviation, fee-aware
per-swap output, gross operation retention, caller floors, marginal LP, final
idle/allocation and callback captures protect different quantities or moments.
Their percentages are not summed into a budget. Retaining financial valuation
requires healthy prices even if spot-agreement bit2 is disabled. Retained
samples likewise require their condition/control data. These necessary
dependencies are documented instead of silently weakened.

Expected normal blockers include poor execution/liquidity, infeasible optional
residual geometry, retained stale samples, reference disagreement and accumulated
idle. Recovery must use the explicit reviewed operation, not entrant subsidies
or an automatic weaker retry. No further unintended conflict was established in
this scoped review; this is not an exhaustive-state or exploit-absence claim.

## Verification and remaining risk

[Verification](VERIFICATION.md) records85distinct selected contract successes
across explicit stages,47focused Python passes,43normal size gates, unchanged
ABI/storage semantics and fresh static output with scoped review/reuse. Initial
failures, the callback mismatch and an empty diagnostic selection remain.

Mask0 can lose nearly all principal; valid raw LP can be inactive, and positive
user floors can still reject. A broken asset/core cannot be repaired by bypass.
Runtime pins changed with unchanged ABI/storage/capability getters; old installed
contracts/services/journals acquire none of this behavior. Actual prices/routes,
governance wallet, target gas/economics, service/recovery rehearsals and independent
audit/remediation remain open. No service, website, Anvil, signer or public funds
were changed.
