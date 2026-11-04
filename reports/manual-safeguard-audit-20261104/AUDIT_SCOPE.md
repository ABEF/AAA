# Manual recovery and normal safeguard composition: revised audit prompt

Baseline main0b14aca; isolated local execution only. Preserve Anvil8902, all
wallets/NFTs/LP/balances, served sites, services, journals and paused heartbeat.
No public transaction, deployment, sealing, service restart or signing extension.

## Clarify and challenge the two objectives

1. Map every operator intent to its actual authority, function, prerequisites,
   outputs, reversibility and residual/fee/share consequences: normal keeper-grant
   rebalance; paused emergency active/parked redeployment; main+residual merge;
   residual-only closure; full parking; ordinary resume/same-pair move; harvest,
   compound and buyback; stop/restart/configuration; terminal owner return; and
   pre-exit canonical preparation/draining. Explain which calls are truly force
   paths. Remove unintended OPTIONAL timing/economic blockers from explicit
   governance emergency choices, not authorization or exact accounting.
2. Trace safeguard dependencies and execution order across contracts and worker:
   trigger, same-side reference, sampled window/gap, hard cooldown, local jitter,
   source agreement/freshness, spot deviation, gross/additional/caller floors,
   aggregate retention, idle/main allocation, raw close minima, pause/flags,
   snapshot/revisions, allowance/callback/receipt checks and recovery. Distinguish
   useful overlapping checks at different moments from accidental coupling.

"Never blocked" is physically impossible with a broken token/core, nonexistent
liquidity, insufficient actual assets or gas. Force must not revive terminal LP,
rewrite NFT rights/shares/reward reserves, bypass canonical ownership locks or
send principal to an operator. Forced recovery can deliberately lose almost all
principal; it is never an automated fallback. Normal user/keeper guards stay.

## Second critical review

- Timing bit1 and sampled-evidence bit16 are separately selectable. Test whether
  retaining samples silently reintroduces a disabled hard cooldown.
- Pool inventory can change asset sides between reviewed snapshot and inclusion.
  Test an explicit paused-governance raw close with both optional output floors
  zero while preserving authenticated physical/current receipt proofs.
- All-zero emergency must work from Active AND Parked with bad USD sources,
  stopped ordinary confirmation, disabled operations, empty automatic router and
  unusable optional residual geometry, when the core itself remains executable.
- Positive controls must still fail with retained protections; raw minimums,
  stale hashes, deadlines, sender, shares, callbacks and terminal locks remain
  independently checked. Follow a failure with an actual recovery, not just revert.
- Inspect mandatory native-pair/LP ownership, exact receipt/burn/mint and range
  feasibility checks before calling an unavoidable failure a policy deadlock.
- Reuse exact unchanged evidence. Run causal regressions first, then only affected
  methods; compile new normal sizes/reference/static scope for actual source edits.
- Update one operator procedure, sole Todo, feature/evidence/findings/release and
  repository context. Preserve prior report bytes and failed stages; source
  publication is not rollout or production approval.
