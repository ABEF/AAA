# Ubuntu supervisor interruption and recovery — 25 November 2026

Two NEW isolated partitions complete stock keeper/Cast recovery under native
systemd supervision. Both actual model results and the separate saved-vector
reviews pass. This is finite same-host evidence; Q06/P20/P21 and production
approval remain open.

The source snapshot is `7f862557df8e8cbaf8494c7b1c12f18e07be436d`, with all190
packaged production members unchanged. Frozen F6 source/dependency/control maps
remain61/39/4 and1,021ABI rows. Disposable encrypted local signers and copied
Anvil state run unprivileged in a private network. The ordinary240-second poll,
12confirmations, hourly harvest,24M/full25%,5gwei,0.01ETH transaction and0.05ETH
daily limits remain. Each lab retains its6,000RPC/900-second work bound.

## Saved-hash watchdog: c804

[c804](evidence/c804/model-RESULT.json) completes in2,932RPC. After the real Cast
transaction hash is durably saved, the peer completes HTTP headers and sends121
single-byte fragments without finishing the chunk-size line. The incomplete
response lasts122.041seconds; no completed HTTP reply or synthetic progress
notification is supplied. The loaded120-second watchdog records an actual
`watchdog` failure and one automatic restart.

The [native proof](evidence/c804/native-NATIVE_RESTART_PROOF.json) retains38
samples. The old cgroup is observed empty before the replacement main starts;
the original lock inode is available exclusively during that gap and is reused.
Four raw pending-journal snapshots match exactly. The stock daemon recovers the
same hash without another send, then completes a fresh `healthy_v2` normal
cycle. The captured old group contains only the main process: this saved-hash
watchdog case does not demonstrate active-Cast cleanup.

## Active Cast, deliberate main kill: c806

[c806](evidence/c806/model-RESULT.json) completes in2,357RPC. The node accepts
the original signed transaction, while a controlled peer withholds its hash
reply from the still-live real Cast child. Root-native inspection authenticates
that child's process generation and separate session, then deliberately sends
SIGKILL to the keeper main only. The manager records a `signal` failure. Six
[native samples](evidence/c806/native-NATIVE_RESTART_PROOF.json) show the old
main/Cast generations dead and the cgroup empty before one automatic restart.
The same lock inode and exact hashless journal survive; ordinary stock restart
reports `recovery_required` and sends nothing further.

The explicit nonsigning stock `--resolve-pending` command adopts only the
independently captured accepted hash. Its root-owned
[completion record](evidence/c806/native-RESOLUTION_COMPLETE.json) comes from
successful bounded `systemd-run --wait`, even though the completed resolver's
transient properties have already been collected. The stopped keeper definition
is also collected; [normal resume](evidence/c806/native-NORMAL_RESUME.json)
recreates the exact reviewed unit with the same configuration, settled journal
and existing append log paths. Append policy is source/property evidence, not
an independent comparison of prior log-prefix bytes. The recreated unit's
restart counter is separate from the earlier automatic-restart proof. A fresh
stock healthy normal cycle completes.

This is manual-main-kill cleanup, not a Cast watchdog or90-second signer-timeout
experiment. Killing the signer does not cancel its accepted transaction.

## Exact recovery and evidence limits

The independent [c804](evidence/INDEPENDENT_C804.json) and
[c806](evidence/INDEPENDENT_C806.json) reviews each execute once over saved
vectors only. Each case has one original raw submission,300,814gas, canonical
8wei/gas and exactly2,406,512wei paid, against the original captured maximum
414,080,002,898,560wei. Transaction/receipt/header identity,12-confirmation
depth, nonce0→1, canonical anchor, inclusion-day spend and harvest clock agree;
no resend or double charge occurs. These are controlled Anvil fees, not target
provider qualification. Original schema1 remains selected.

Both cases retain equal two-NFT owners/shares/membership/royalty weights, main-LP
identity/liquidity/ticks/custody and captured financial projections. No new
swap, contribution, claim or nonzero fee-allocation journey is qualified. Saved
local keeper-grant envelopes/events are consistent; before/after role getters
and the grant's canonical header are not supplied. Permissionless harvesting
is not proof of keeper authorization.

Final raw journals are captured only after shutdown, with exact bytes and SHA
sidecars retained. Their settled critical fields match recovery. Later ordinary
changes are explicit: c804 `conversion_turn`/`observed_adjustment_v3`, c806
`conversion_turn`; final bytes are not relabelled as the earlier recovery bytes.

The earlier c805 payload was installed but never started. Static review found
that clean transient-unit collection could discard stopped-unit definitions or
resolver exit properties. The correction affects only the new private c806
controller; the original unused payload/provenance remains preserved. No
production code/default/unit changes; zero unchanged test bodies or old passed
journeys rerun.

The [public evidence manifest](verification/EVIDENCE_MANIFEST.json) pins the
captured vectors, controllers, fixture helpers and independent verifier sources.
The complete original input archives remain private, outside Git; full source
replay uses those exact hash-bound archives as `--build-dir`, rather than
substituting current files or recreating the original state. The public saved
vectors and verifier results retain their own exact hashes. No signing material
is included.

The workload guide's stale 2,002-definition count and old inventory-check command
are corrected to the unchanged current 2,003-definition inventory. Todo statuses
remain 35 implemented locally,40 in progress,7 to do and1 excluded; no release
gate is closed by these checks.

## Cleanup and remaining work

Per-lab [c804](evidence/c804/control/STOP.json) and
[c806](evidence/c806/control/STOP.json) stopped readbacks are supplemented by
the final fixed-path capture of all nine new unit names: every main PID is0
and every recursive cgroup is empty, including unused names. The separate
[host comparison](evidence/HOST_PRESERVATION.json) preserves five original
service states and seven previously stopped labs, with zero non-ambient
differences; one pre-existing observer invocation change remains explicit.
Existing chains/Anvil8902, NFTs/LP/balances, journals, websites, signer restrictions
and the user-paused heartbeat remain unchanged.

DNS stalls, storage/WAL/fsync/permission failures, restart storms, off-host
restore/fencing, alerts, combined scheduling/soak, actual providers/complete
fees/markets and independent release approval remain open. Earlier Q06
header/failover/inert-signer results and their raw cgroup warning retain their
original scope. Source/evidence publication adopts no running service or journal.
