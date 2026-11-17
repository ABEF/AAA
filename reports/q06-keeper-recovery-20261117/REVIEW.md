# Q06: isolated keeper interruption and recovery

Baseline main: `44f5a650ae7abfb40cab810e389a393e526130ca`.

**Two confirmed operational defects are fixed. Twelve distinct new unit methods
pass. An actual Linux/systemd rehearsal verifies the finite interruption and
recovery cases below. Q06 remains in progress for release-specific operation;
this is not service rollout or production approval.**

## Availability and isolation

Windows has no installed WSL distribution or local container runtime available
for this rehearsal. The existing authorized Linux host supplies Python3.12.3,
kernel6.8.0-137-generic and systemd255. Transport/setup used existing authorized
administrator access; every test worker ran as unprivileged `nobody` in a NEW
transient unit, private network and owned directory. No key material was copied
into the fixture. Dummy credential files and an inert executable replace Cast:
it cannot sign or send a transaction. All HTTP peers are synthetic loopback peers.

Selected source unit settings remain120s watchdog/120s group-stop/30s restart,
with main-only notifications, SIGKILL, no core dumps and bounded starts. Extra
test containment limits CPU20%, memory192MiB, tasks24 and runtime480s. Loaded
properties and actual manager lifecycle records are retained; they do not prove
an installed production unit has the same effective settings.

## Confirmed fixes

| Finding | Reproduced failure | Correction and verification |
| --- | --- | --- |
| Stop during durable intent publication | A stop arriving inside the actual atomic save still launched the signer afterward. | Check the cooperative stop flag immediately before signer launch. Retain the exact hashless intent, nonce and fee review for reconciliation. Three new methods cover the regression, normal submission and a post-publication storage error. Actual Linux SIGTERM during save launches zero inert sends. |
| Healthy bounded failover falsely expires the watchdog | Eight endpoints can each complete bounded reads while the outer logical RPC exceeds120s. Only reporting completion of the outer call incorrectly stops this progressing operation. | The keeper explicitly wires a synchronous optional HTTP-completion hook. No pulse occurs inside blocked I/O, no timer thread is added and a late watchdog error remains fatal. Nine new methods cover progress, blocked/late reads, budgets, retry cause, default-inert clients and actual main wiring. Actual Linux failover lasts127.445s, completes16 HTTP replies and does not restart. |

This changes no retry/timeout/gas/financial default, signing authority, journal
schema, nonce policy or automatic resend behavior. The shared Rpc defaults to no
hook. A signal can still race a later machine instruction: this is cooperative
shutdown at the final observed boundary, not transactional signal cancellation.
The surviving hashless intent deliberately blocks new work, even when this
particular test knows the inert signer was not launched.

## Actual Linux process outcomes

| Case | Observed result | Boundary |
| --- | --- | --- |
| Durable hash and receipt recovery | One inert send; canonical synthetic receipt accounts nonce0→1 and300wei exactly once; another recovery leaves state bytes unchanged. | Actual HTTP/process/atomic state code, synthetic transaction/event/fees; no EVM, real signature or Robinhood fee qualification. |
| SIGTERM during save | Exact saved hashless bytes survive, nonce0, empty spend, zero inert sends and no automatic restart after intentional stop. | Actual handler/save/submit path; no automatic intent deletion. |
| Header trickle with no completed request | Native manager records `UNIT_RESULT=watchdog`, kills the main process and restarts once. The same lock inode is reacquired. A concurrent lock contender fails. | Incomplete headers send bytes every second, so this exceeds socket-inactivity behavior. DNS and body-trickle variants are not separately executed. |
| Kill main while signer descendants remain | Inert signer and detached-session grandchild both ignore TERM; manager kills both before the new main starts, about30s after group cleanup. Original hashless journal/nonce/spend survive, with one original inert send. | Deliberate SIGKILL of main, not a signer watchdog/90s-timeout experiment. Descendants remain in the test cgroup despite session detachment. |
| Completed HTTP failover | All16 bounded replies complete over127.445s with watchdog120s, zero restarts. | Real Linux elapsed time/HTTP, synthetic responses, not external-provider qualification. |

Restart uses an explicit **test-only recovery dispatcher**: the new Keeper
revalidates its current profile and only reconciles pending state/checkpoints.
It schedules no new maintenance. This proves recovery/locking without exposing
an accidental send; it does not establish the complete stock daemon's healthy
maintenance cycle. The separate new hashless-intent method exercises the real
ordinary cycle's pending-first block.

The RPC manager log includes `Failed to kill control group ... Invalid argument`
after killing its main process. This warning is retained, not rewritten into a
clean result. That case has no extra signer descendants; the separate signer
case records both descendant kills before restart. All15 owned units across the
campaign and preparatory attempts are finally inactive, PID0 and empty cgroup.
This is specific process evidence, not a universal host/cgroup guarantee.

## Evidence and preparatory failures

[VERIFICATION.json](VERIFICATION.json) indexes source stages and results.
[EVIDENCE_PEER_CHECK.json](EVIDENCE_PEER_CHECK.json) independently checks the raw
archive, source maps, state hashes, unit cleanup and manager ordering.
[process/EVIDENCE.tar.gz](process/EVIDENCE.tar.gz) contains the bounded native
receipts, synthetic HTTP/state transcripts and selected manager messages.
Its manifest authenticates149 other files; supplied source pools have separate
before/after maps. All maps are unchanged:462files for the first attempt and
463 for each later attempt. The current campaign uses the exact source hashes
in its manifest, including the current two fixes.

Three preliminary stages remain visible, never counted as extra passes:

1. A missing public event-schema fixture blocks import; the next bundle includes it.
2. A separate unprivileged preparation succeeds, before the complete campaign.
3. `/run` is mounted `noexec`, so the inert executable cannot start. The new owned
   campaign moves to executable `/opt`; no mount protection is changed. Real
   keystore/password data can remain on a `noexec` filesystem.

Earlier evidence retains its exact source stage. The three intent methods
precede the unrelated main-RPC wiring line; the final nine-method stage and Linux
bundle include both fixes. Counts overlap between red/green stages: **3+9=12 new
distinct methods**, not every recorded invocation added together. No unchanged
test method, old process campaign, Solidity build/test or public RPC campaign
is rerun. The maintained keeper inventory lists the new methods while executing0.

## Preservation and remaining Q06 work

No installed unit/configuration is written or controlled. Existing Anvil8902,
NFTs/LP/balances, application journals/DBs, signer, websites and the user-paused
desktop heartbeat are not changed. New test state stays inside the owned labs;
their units are stopped. Existing server timers continue independently.
Before/after observations show a changed inactive observer InvocationID; its
PID1 lifecycle messages and existing five-minute timer explain intervening
normal exports. Therefore we do not claim every host observation or naturally
changing live journal was byte-identical. No installed application journal or
credential contents were collected.

Q06 still requires the selected release's actual encrypted Cast/keystore and
contract/provider configuration; full normal daemon scheduling/recovery; stalled
DNS/body variants; disk/permission exhaustion; off-host backup/restore, fencing
and alert delivery; restart-storm/host-loss/key-rotation and sustained operation.
Actual authorities, markets, complete target fees, service rollout and independent
approval stay open. Preserve the original64-row registry and its dispositions;
these two new defects and finite operating receipts do not resolve every row.

See the [operator procedure](../../docs/OPERATOR_MANUAL.md#keeper-interruption-and-recovery-q06),
[detailed recovery runbook](../../docs/KEEPER_RECOVERY.md#stalled-rpc-and-progress-watchdog)
and [sole Todo](../../TODO.md#task-keeper-recovery).

Primary references: [systemd service watchdog/restart](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html),
[process-group termination](https://www.freedesktop.org/software/systemd/man/latest/systemd.kill.html).
