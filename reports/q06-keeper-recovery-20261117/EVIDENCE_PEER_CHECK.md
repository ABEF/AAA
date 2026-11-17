# Independent review of collected Linux evidence

This review reads the already-collected local evidence and harness sources. It
does not rerun a test, contact the host, control a service or change runtime state.
`EVIDENCE_PEER_CHECK.json` records the independently recomputed file/state checks.

## Supported conclusions

- All 149 collected files match the archive manifest digests. The four runs'
  supplied-source before/after maps agree exactly: 462, 463, 463 and 463 entries.
  These are the scoped source-preservation records, not a hash of the entire host.
- All 15 owned transient-unit final records report inactive, MainPID zero and
  empty control group, including failed/preliminary attempts. Their evidence is
  retained separately rather than counting preparation as campaign success.
- Main campaign `popl-q06-20261117-7b5ec836608b` uses real Linux/systemd255,
  Python3.12, unprivileged workers, private networking, HTTP, flock, durable file
  writes and notification sockets. Loaded-unit records contain the intended
  120-second watchdog, main-only notifications and control-group kill policy.
- The incomplete-header trickle causes an actual manager `watchdog` failure and
  SIGKILL, followed by one restart. A contender demonstrably fails on the held
  flock. The succeeding worker acquires the original lock path; the supervisor
  records that its inode is unchanged.
- Manager monotonic records place killing the inert signer and its independently
  sessioned grandchild before the next signer-service start. Final SIGKILL follows
  the configured 120-second stop timeout; the new start follows roughly 30 seconds
  afterward. This is evidence for these processes, not arbitrary descendant trees.
- The signer restart retains the exact hashless journal digest recorded at its
  first inert send: nonce0, no recorded spend, one send. Recovery reports
  `broadcast_ambiguous`; it does not send again.
- The stop-during-save case retains matching pre-stop/final state digests, nonce0,
  empty spend and zero inert sends. The actual systemd stop produces the new
  `shutdown_after_intent_before_signer` event.
- Saved-hash receipt recovery has one inert send overall, clears pending, advances
  nonce to1 and records exactly300wei (100gas × 3wei), matching the saved marker's
  state digest. The harness's repeated recovery checks leave that state unchanged.
- A 127.44-second finite failover call finishes under the 120-second watchdog
  because completed transport attempts notify progress. The synthetic successful
  result and individual completed replies are recorded; no real provider is
  qualified by those responses.

## Qualifications and retained warning

The RPC unit's manager journal includes `Failed to kill control group ...
ignoring: Invalid argument` immediately after its recorded main-process kill.
The main process then exits9, recovery acquires the lock and the final unit is
inactive. The separate signer case contains explicit descendant kills before
restart. Retain the warning and do not describe all manager logs as warning-free
or infer universal control-group cleanup from this single RPC process.

The existing observer's InvocationID changes during the campaign. Its recorded
five-minute timer and manager start/finish entries explain the observed activity;
the snapshots end inactive. This does not support a claim that all existing host
bytes, output journals or invocation identities remained unchanged.

Contracts, runtime pins, prices and receipts are synthetic; Cast is an inert
program with no signing implementation. Startup exercises real permission and
transport checks against those placeholders, not actual encrypted-key usability.
The restart dispatcher intentionally performs recovery-only work and does not
qualify unrestricted steady-state scheduling, live market/fees, production
configuration, off-host alert delivery, DNS stalls, every body-trickle case,
restart storms, host/storage loss or multi-host fencing. The 120-second stop
timeout leaves a real delay before stubborn children die; an actual transaction
could already have been broadcast. Preserved ambiguity must not be represented as
cancellation or permission to resend.
