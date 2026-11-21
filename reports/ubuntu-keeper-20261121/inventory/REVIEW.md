# Read-only Ubuntu rehearsal host inventory

21 November 2026. This inventory starts no new environment, unit or daemon and
changes no service configuration/control, application recovery journal,
credential or installed tool. Normal SSH audit logging can still occur.

The local `wsl.exe --list --verbose` reports that WSL is not installed. Docker
and Podman command entry points are absent. The existing SSH transport reaches
the previously authorized46.225.185.212 host with strict pinned-host checking,
batch authentication, the existing externally stored key, no agent, no PTY,
no forwarding and no automatic host-key update. Credential bytes are not read
by the inventory scripts, printed or included here; OpenSSH performs authentication.

Current host: Ubuntu24.04.3LTS, kernel6.8.0-137-generic, Python3.12.3,
systemd255 (255.4-1ubuntu8.18). Native Anvil/Cast/Forge1.4.4 executables exist
under `/opt/zzz-keeper-staging/bin`; exact versions and digests are captured.
There is no discovered Solc/container CLI. `/opt` is executable and has about
62.5GB free; `/run` is `noexec`. Available RAM is approximately7GB.

The native binaries are mode0755 and owned by UID1001, so their owner can mutate
them despite root-owned0755 parent directories. The proposed rehearsal should
copy only these public, hash-verified tools into a NEW root-owned readonly lab
directory and verify the copied bytes. Do not modify the installed binaries or
mount protections. Existing private signing material is outside this inventory.

Before any new rehearsal work, nginx is active (PID3557118, restart count0),
the historical staging Anvil is already failed (PID0, restart count6), the
historical keeper is inactive, and its observer timer is active. Port18545 is
not listening. These are observations, not permission to repair/restart staging.
Existing web/SSH/observer processes and unrelated TCP8443 remain outside scope.
The user-paused desktop heartbeat is not resumed. Observer InvocationIDs may
change naturally as its existing timer fires; do not claim byte-identical host
activity solely from this snapshot.

`HOST_PROBE_RAW.json` is the exact remote stdout whose digest is recorded in
`HOST_PROBE_EXECUTION.json`; `HOST_PROBE.json` is a separately normalized rendering.
`host_probe.py` is the exact executed read-only remote source. The permission
probe and output are separately retained. [Manifest](MANIFEST.json) binds the
sanitized original files. Raw local command captures also remain in the external
owned inventory directory. This is platform feasibility, not keeper or release
qualification, and no contract/service test is counted as passed by inventory.
