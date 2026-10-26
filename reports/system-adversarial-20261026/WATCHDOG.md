# Keeper stalled-I/O containment

## Confirmed availability gap

Socket inactivity timeout is not an absolute DNS/header/body deadline. The actual
RPC transport can remain inside `urlopen`/buffered `read` while a peer trickles
data. Previously the main keeper called this directly, without a process deadline.
`Restart=on-failure` alone does not restart an alive blocked process, and the
health file/off-host check can detect stale work but cannot interrupt it.
The API already has separately killable30second request workers.

This can stop harvesting/rebalancing/conversion progress. It does not by itself
grant token transfer permissions, change shares or enable an automatic resend.

## Source-only correction

- Optional [ProgressWatchdog](../../keeper/watchdog.py) consumes reviewed systemd
  notification environment during startup. Unconfigured commands remain the old
  standalone path; a valid mismatched PID is ignored like systemd's convention.
  Invalid configured values fail with fixed sanitized messages.
- The main process emits an initial pulse before Keeper construction. Enabled
  construction receives an actual Rpc wrapped in ProgressRPC, so live startup
  validation reads also make progress. Both `.call` and `.eth_call` report only
  after a read completes or returns an error. Delegate-only `.eth_call` would
  bypass the wrapper; independent review caught and corrected that omission.
- Main-loop boundaries and intentional interruptible one-second polling sleep
  report progress. No background timer/thread can conceal blocked DNS, headers,
  body reads, signing or CPU work. A late return cannot locally revive progress
  after the watchdog's expected deadline.
- Cadence is at most10seconds while progressing, or one third of a shorter
  timeout. Force pulses bracket startup and cycles. The120second example leaves
  margin for the existing90second bounded cast step; manual interval overrides
  need operating review against all legitimate uninterrupted steps.
- Notifications contain only fixed `WATCHDOG=1` bytes, use nonblocking Unix
  datagrams and close their socket. Notification errors are terminal/sanitized.
  Notification credentials are removed before signer children are created;
  NotifyAccess=main and captured-PID checks also restrict who can report progress.

The [example unit](../../keeper/zzz-keeper.service) remains Type=simple/dry-run,
with WatchdogSec=120s, NotifyAccess=main, WatchdogSignal=SIGKILL, control-group
termination, explicit final SIGKILL and LimitCORE=0. SIGKILL avoids the default
watchdog SIGABRT/coredump path and cannot be swallowed by the keeper's graceful
stop handler. The existing120second stop timeout and Restart=on-failure remain.
No financial method, allowance, parameter, journal layout, nonce or recovery rule
changes. Previously persisted ambiguous intent remains pending; restart uses
the existing reconciliation path and never automatically resends it.

## Verification and limits

Development scope:21new methods,20passes and one actual Unix-datagram skip on this
Windows runtime. Inert clocks/sockets cover PID/encoding/env validation, fixed
payload, nonblocking/failure/late/fork behavior, cadence/signing margin, transparent
RPC methods, initial live-constructor ordering, once/init/resolve dispatch,
intentional idle stop and required unit properties. The `.eth_call` composition
test uses actual Rpc code with only `_post` replaced; no endpoint/signature is used.

The initial19method development run had12fixture errors because the inert socket
fixture had not supplied AF_UNIX on this Windows runtime. Production correctly
rejected unavailable transport. Tests now supply that symbolic identity only
inside mocked-socket cases; the actual Unix test stays skipped. First source and
terminal result identities are [preserved](watchdog-attempt1/terminal-result.json),
also archived externally under `system-watchdog-20261026/attempt1`, with no repeated failed run and no assertion
relaxed. Root's final244method selection (241 passes/3 explicit skips) supersedes this
overlapping development count and pins the frozen candidate.

**Not an absolute deadline without the reviewed Linux supervisor.** Standalone
keeper commands still use the existing socket/retry policy and can block in
upstream OS I/O. A progressing but slow cycle can last longer than120seconds;
this watchdog detects lack of progress, not an overall cycle-duration SLA.
Notify delivery/local unit text are not proof of actual cgroup cleanup/restart.

Before enabling an actual service, qualify systemd>=240 and inspect effective
WatchdogUSec/WatchdogSignal/NotifyAccess/KillMode/SendSIGKILL/FinalKillSignal/LimitCORE.
An older manager may ignore unsupported settings and must not be declared
protected. Rehearse stalled DNS/header/body reads, signing interruption, all-child
termination, lock release, pending-journal preservation and no-overlap recovery
on the exact Linux host. Retain off-host health alerts; the user's paused
monitoring is unchanged. No installed unit, service, signer, existing Anvil,
website/server, journal, balance or public transaction was changed here.

Sources for supervisor semantics: systemd's
[service watchdog/restart](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html),
[notification/PID environment](https://www.freedesktop.org/software/systemd/man/latest/sd_watchdog_enabled.html),
[sd_notify](https://www.freedesktop.org/software/systemd/man/latest/sd_notify.html)
and [group-kill/watchdog signal](https://www.freedesktop.org/software/systemd/man/latest/systemd.kill.html)
manuals. Actual installed manager behavior remains an operating rehearsal gate.
