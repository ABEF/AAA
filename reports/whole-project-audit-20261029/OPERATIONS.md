# Keeper, operations and delivery review

Source baseline main781fcc9; final source fixes and explicit later240-second
user decision are listed below. No installed service, journal, signer, monitor,
Anvil or public host was operated. Phase1 maps/pins and raw receipts are external
under `whole-project-audit-20261029/operations`.

## Demonstrated repairs

**Metadata restart fairness.** The old cycle flipped `next_first` only in memory
before optional metadata RPC. Losing the process before a later save could
restart the same blocked metadata ahead of every LP opportunity. The repair
clones/saves the turn before optional work, after pending recovery. A simulated
process loss followed by reconstructing the worker solely from its real saved
journal now leaves a due `Vault.collectFees` opportunity. Save failure stops
before metadata/submission and restores memory; if an atomic replace completed
before a later filesystem error, disk may contain the advanced priority bit.
That is not a nonce/spend/financial-state rewrite. Preserve and reconcile the
file; do not promise universal disk rollback. Cost: one deliberate atomic save
per reached enabled metadata turn. Real supervisor/disk-failure rehearsal stays open.

**Four-minute confirmation schedule.** The user approved240-second checks while
retaining on-chain900-second duration/strict300-second maximum gap. The earlier
schedule anchored to a snapshot `s`; if inclusion delays are `d1,d2` and next-poll
overshoot `e`, successive observation gap was `300+e+d2-d1`. It preserved the
window only when `e+d2<=d1`. New scheduling changes300to240 in that expression,
leaving roughly60seconds; it does not guarantee progress or add on-chain grace.

Original300 and new240 journal deadlines are both validated, without rewriting
on construction or pending recovery. Effective next check is no later than
`last_checked_at+240`; successful ordinary evaluation writes240. Nonce, original
review, pending hash, spend, clear/reset acknowledgements and jitter remain.
Startup/foreign evidence still requires authenticated reset, not adoption.
Source config now requires explicit poll60-240. Reconcile pending with the old
reviewed release first; a config using300needs deliberate reviewed reduction
before source rollout. Health writer/checker requires matching240 cadence; no
existing worker/config was changed. Observing during cooldown remains proposed.

**Dedicated keeper selection.** The list omitted newer keeper regression modules,
although full `verify.sh` separately discovers the wider suite. The maintained
list now covers current keeper modules and shared RPC/state/native helpers.
Defined classes are deduplicated; duplicate modules/method IDs, foreign identity
or empty modules reject explicitly. `--list --output <new.json>` inventories
without executing bodies, clearly reporting `execution_performed:false` and zero
executed methods. This is not a613-or-later-method fresh pass; final inventory
and executed identities are in the verification summary.

**Fork CI scope.** The committed job labelled current still selected historical
fixtures. It now calls the independent current native-pool runner, with the
official checksum-pinned compiler verified before execution. Existing runner
checks normal compiler/profile/Forge identity and exposes only read RPC methods.
The old dirty runner/tests remain untouched. Static wiring checks are not a
compiler download, GitHub workflow or real fork execution; those are unrun here.

## Reviewed paths and limits

Deeper source tracing covered discovery/version admission, pending-first intent/
sign/receipt/checkpoint/fee budgets, confirmation/reset/jitter, harvest isolation,
buyback/conversion/principal job fairness, metadata, locks/atomic journals,
watchdog main-progress notifications, health pins, preflight/snapshot recovery,
CI selection, dependency installer/build gates and local-only deployment boundary.
No extra authority, external custody, bridge or public signing path was added.
LP claim, harvest, compound, buyback and principal payouts remain distinct.

The563Python callable inventory across65files is navigation, not563independent
body reviews. Secondary historical local launcher/rehearsal/artifact CLI paths
not fully retraced retain that limitation. Existing process rehearsal and staging
are historical mock profiles; no current4 Linux/host/target-chain qualification
can be inferred. Recovery after key/host loss still needs real old-host fencing,
complete pending/cost evidence and operator review, not rediscovery alone.

New checks use deterministic/inert RPC and temporary files. Metadata interruption
uses an injected process-loss exception, not an actual operating-service kill.
The final23new methods and17affected existing methods pass with network and
subprocess blocked; raw negative controls and superseded attempts remain.
No old399-method suite was repeated. See [verification](VERIFICATION.md) for
the exact final pins, distinct counts and actual unexecuted operating gates.
