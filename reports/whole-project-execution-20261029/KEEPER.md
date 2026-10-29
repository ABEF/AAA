# Keeper operational review and focused repairs

Scope: current intentional confirmation2/emergency1 working candidate on main,
plus preserved historical keeper profiles. No service, signer, operating journal,
Anvil, website, public transaction or deployment was changed. No network provider
or real wallet was used. This is an internal source review and fixture evidence,
not production approval or independent whole-project assurance.

## Repaired behavior

1. **Existing confirmation work could lose its nonce opportunity to optional
   jobs.** A tracked240-second check was reached only after conversion/buyback/
   metadata priority. With a strict300-second gap, eventual queue fairness was
   insufficient. `_confirmation_priority` now runs after pending recovery and
   shared accounting/lifecycle/seal/keeper gates, before optional nonce users.
   It services existing reset/clear/check/jitter deadlines in earliest-deadline
   order through the original guarded submission path. Cold discovery and time
   between checks retain ordinary queue fairness. A blocked priority attempt is
   not repeated later in the same cycle; independent work remains available.
2. **Unrelated optional degradation stretched polling.** Health remains degraded,
   blocked counters and consecutive failures remain visible, but `poll_delay`
   keeps the configured outer poll for known confirmation state when the cycle
   completed without a global error. Actual cycle-level RPC/recovery faults and
   nonce reconciliation keep exponential backoff. No cost limit or retry clock
   is removed.
3. **Clock retreat could hide a deadline.** Independent review reproduced a
   primary head below the record's last check: the deadline appeared future and
   optional work ran first. Both the primary head against known records and a
   secondary fresh head against the primary now fail the entire cycle and
   durably invalidate known windows before optional jobs. Pending recovery still
   precedes these reads. The old clock regression now expects this stronger
   global failure boundary rather than a bucket-only deferred error.
4. **CLI configuration used permissive JSON.** Keeper main now uses the shared
   strict `read_json` and requires a JSON object before Keeper construction.
   Duplicate/nonfinite recovery-state parsing and atomic writer hardening belong
   to the backend agent's separately recorded shared-state repair. No journal is
   silently repaired or rewritten.

Changed keeper-owned files: `keeper/monitor.py`, new
`tests_python/test_keeper_confirmation_priority.py`, strengthened clock assertion
in `tests_python/test_keeper_confirmation_incidents.py`, and the dedicated keeper
runner/inventory to include priority plus `test_state_json_integrity`. The
original intentional dirty candidate was preserved; `monitor-task.patch` compares
only this task against `monitor-before.py`.

## Evidence

- `focused-final.json`: **21 distinct new methods pass**, no failures/skips,
  unchanged source hashes during the run. Covers busy optional queues, outer240,
 239/240/300/301 boundaries, cold/not-due fairness, due jitter, resets, earliest
  deadline across buckets, pending-first, save/clock/routing/authority failures,
  failure telemetry, global RPC/nonce backoff, strict CLI JSON and confirmation2
  disagreement. No contract timing/economic policy was relaxed.
- `integration-final.json`: **43 distinct existing affected methods pass**, no
  failures/skips, unchanged source hashes during the run. Includes legacy300
  schedules, clear acknowledgements, raw versus unrelated failures, canonical
  pending/nonce/spend guards, buyback/metadata/holder-delivery fairness and exact
  runner selection. The21 and43 method identities do not overlap. `summary.json`
  records their union and verifies current keeper/shared production pins.
- The first negative run selected12 methods and produced **11 failing
  assertions/subcases across7 distinct methods**, not11 separate tests. Queue
  displacement and480-second polling versus the expected60seconds were concrete
  failures. `negative-before.log` preserves them.
- `negative-clock-retreat-before.log` separately preserves the independently
  discovered primary-clock counterexample. `negative-cli-before.log` preserves
  ambiguous config reaching a mocked constructor before strict parsing.
- Retained intermediate attempts: `focused-first-18` has one fixture error from
  missing reviewed compounder pins; the fixture was corrected rather than
  weakening runtime checks. `integration-first-43` has the obsolete bucket-only
  clock expectation; its updated assertion is stronger. `affected-first.log`
  records123 earlier overlapping passes and is not added to the final64 count.
  `focused-clock-19` and the first12-pass log are overlapping intermediate
  evidence, not extra coverage. Initial PATH `python` was unavailable; bundled
  Python3.12.14 was then used.
- `body-review.json` lists153 named/nested body rows across11 owned/support
  modules with locations and hashes. These rows are static review navigation,
  never execution tests. Review includes serial recovery, actual receipt costs,
  compound/harvest, conversions, metadata, terminal delivery, operational health,
  snapshots, watchdog, RPC, fee derivation and versioned Position readers.
- `git diff --check` passed for the keeper-owned edits. No broad Solidity or
  process/service suite was rerun for these Python-only changes.

## Preserved policy and limits

Hard pool cooldown (intended initial12hours),900-second sampled window,
300-second strict gap,240-second source checks,60-600-second post-ready jitter,
manual-width exception, raw-needs compound priority, independent harvest,
economic floors, runtime/capability pins, per-action budget/retry policy and
canonical pending/nonce/spend recovery are unchanged. Manual paused emergency
remains a separate governance path.

An auxiliary share-inventory read outage deliberately blocks financial execution
without resetting independent market evidence; the explicit existing regression
is preserved. Reference disagreement can still indefinitely defer both rebalance
and raw-priority compound. Changing that requires a separate economic decision.

One serial sender cannot guarantee four active windows meet300-second gaps.
Finality, RPC duration, gas/cost caps or competing essential work can still cause
restarts. Priority adds bounded reads for known old scheduling records retained
through cooldown; no automatic journal cleanup/migration was introduced.

Health/source file hashes are diagnostics, not runtime attestation. Matching
health2 writer/checker rollout, actual helper/Strategy/Budget runtime inventory,
target-chain fee semantics, route/provider depth and latency, Unix/systemd
supervision, trusted host fencing, backup restoration and alert delivery remain
separate operating qualification. Windows fixture passes establish none of
those external facts.
