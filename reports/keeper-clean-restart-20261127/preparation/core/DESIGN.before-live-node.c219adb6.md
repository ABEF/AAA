# Stock unsigned keeper restart from a private recovery kit

Design only. No application, test, native CLI, helper or server execution was
performed for this review. Production sources, existing environments and old
journals remain unchanged. Exact current source pins are in `SOURCE_REVIEW.json`.

## Current composition and historical boundary

The historical c814 record retains its original accepted transaction and six
checks. Its original `restore-state.json` is the **pre-transaction** F6 base;
the reviewed c814 model/controller has no producer for a post-inclusion dump.
Saved `CANONICAL.json` is receipt/header evidence, not a loadable chain archive.
Do not resend its old transaction, pretend the base contains its receipt, or
overlay recorded RPC replies and describe that as physical chain restoration.

The newly authorized partition therefore makes one fresh original stock keeper
harvest on a new disposable F6 chain, using the current matching release. Capture
its known-hash pending journal before inclusion, fence the original source and
restart paths, then include that one transaction and retain at least12 actual
confirmations. Capture exact post-inclusion `anvil_dumpState [true]` history.
The target is a separate reconstructed root supplied from persisted desktop kit
files and runs stock unsigned `--once`, followed by one fresh unsigned dry cycle.
No recovery submission, live target, old test body or prior passing composition
is part of this partition. New setup/capture is distinct from old c814 evidence.

## Release and runtime closure

Recursive AST inspection, including imports inside functions and package
initializers, finds31 production/native-CLI files for `keeper.monitor`, the
journal recovery CLI and the health writer's thirteen literal source reads.
All31 match the already reviewed c82141-member release exactly. There is no
`frontend_api`, `indexer` or test-module dependency and no additional repository
JSON resource is needed. In particular, `indexer/event_schema.json` is unnecessary.
Keep the full41-member pinned release if reusing that finite kit inventory; its
four test-source files are inert. Source13 and source19 maps remain exact current
identities; source19 is needed only if scheduler/sidecar records are also used.

c814 differs from current source in `keeper/cast_process.py`, `keeper/ops.py` and
`keeper/recovery_bundle.py`; two of those belong to source13. Do not relabel an
old c814 package with current hashes. New capture binds current source13 and
the actual current recovery-tool provenance; retain the original raw config.

The unsigned target needs Python/stdlib/loader and their precise SONAME mappings.
Reuse only independently checked runtime inventory, recording current versions,
file hashes and exact logical aliases. `fcntl`, socket, tempfile and atomic
directory/file publication support are required. Cast is imported as a Python
helper but its executable is not discovered/called unless `live=True`; exclude
the Cast binary and both signer contents from the target root.

Use stock `python3 -S -B -m keeper.monitor --config TARGET_CONFIG --once` from the
pinned reconstructed release with sanitized environment and no `--live`,
`--initialize-state` or `--resolve-pending`. `-I -m` alone removes the working
directory/PYTHONPATH import route; if `-I` is retained, an independently reviewed
bootstrap must add only the pinned release before running the unchanged module.

## Minimal private inputs and clean-root mapping

| Input | Required binding and treatment |
| --- | --- |
| Matching release | Exact current files, source manifest and source13 map; optional retained source19 map |
| Original configuration | Exact original raw bytes and raw/semantic hashes; never rewrite it to verify the native backup |
| Native journal package | Exactly original `manifest.json` and `journal.json`, external manifest pin, original pending/hash/nonce/fee review/accounting |
| Post-inclusion chain archive | Exact bounded dump with real receipt, transaction and header history; graph/runtime/binding/nonce and financial anchors |
| Separate trust receipt | Pinned capture/helper identity plus original config/package/dump/release hashes retained before accepting transferred kit bytes |
| New target configuration | Separate reviewed file with an explicit difference allowlist; original identities, profiles, jobs and economic/resource limits unchanged |

Keep raw inputs private outside Git. Bound transfer member count, per-file and
total decoded/encoded/compressed sizes; write exclusively, reread persisted
desktop files and build the return transfer from those copies. Do not count a
self-asserted kit manifest as independent trust. Signer files, passwords, setup
key contents, keystore contents and arbitrary host files are excluded.

In a fresh `RootDirectory`, reconstruct the original logical release/configuration
paths from kit copies; mount copied immutable inputs read-only. The original host
application folders must be unavailable. Use separate writable output/runtime
directories owned privately by the unsigned worker. Before launching, require
that the exact restored state file exists, is regular/single-link, matches the
trusted bytes and has the expected pending identity. Unsigned `Keeper` otherwise
uses defaults for a missing journal; that is not an acceptable used-sender restore.

Prefer only the three reviewed runtime changes (`state_path`, `health_path`,
`lock_path`) proven by c814. Preserve the original loopback RPC logical address
by placing a new read-only gateway at that address inside the new isolated network
namespace. If an endpoint change is necessary, list `rpc_urls` explicitly as an
additional infrastructure-only difference and review the exact original/target
configs; do not imply byte-identical configuration. Relative runtime paths resolve
from the keeper working directory, not the config directory. Do not change native
package bytes or use scheduler `rebind` to authorize a source/path/config migration.

Run restored Anvil and its read-only gateway in the new lab's private network;
the target may use only this local isolated RPC. The gateway must reject all send
and admin methods, enforce chain identity, strict RPC IDs and response/work bounds,
and retain zero recovery send/forward counters. No public provider is a fallback.
Fresh locks are new coordination inodes, not proof of old ownership/fencing.

## Recovery invariants and actual time

`poll_pending()` runs before new scheduling. A hashless intent or missing receipt
remains pending and never resends. Recovery requires the exact transaction hash,
sender, nonce, target, calldata, value, chain, signed gas/fee caps and inclusion
identity; receipt gas/cost and fee semantics must fit the original captured
envelope. It verifies canonical depth/header and the previous booked checkpoint,
then repeats header/depth/fee checks before one atomic journal update.

After settlement: pending becomes null, next nonce increments exactly once,
receipt anchor and last fee observation bind the exact inclusion, and original
cost is added once to the **receipt inclusion UTC day**. The pending submission
day, restore day and current wall day are not substituted. An already settled
journal only validates its checkpoint; it must not book again. The second process
must preserve all financial recovery fields, although reviewed scheduling cursors
can advance. Independently check both latest/pending chain nonces and all raw
submission/forward counters before/after the unsigned target.

The first `--once` can continue unsigned scheduling after settling the receipt,
then deliberately exit1 with `degraded` health because a cycle that started pending
does not claim fresh execution/confirmation metadata. Check exact settled state
and that reason. A second fresh process must obtain actual fresh observations
and reach `dry_run_v2`/exit0; an error or unresolved pending does not qualify.

The stock `_head()` requires head time within600seconds of actual wall time.
This is independent of native backup capture-age review (for example86400seconds)
and any900-second operating backup freshness. Do not backdate wall time, monkeypatch
time, rewrite old blocks/journals or relax those guards. New setup uses real time;
preserve its actual capture/inclusion timestamps. If a copied local chain becomes
stale, ordinary empty mining may advance **new** local heads while preserving old
receipt/header history; record that action and do not call the restored fork
current public canonical truth. Record the actual original policy and capture age
rather than assuming the older fixture's900-second policy applies to this new kit.

## Required fail-closed witness

Require exact source/manifest/config/package/dump identities; a present restored
journal; explicit profile and complete code/binding identity; real current head;
original fee review, confirmations and canonical inclusion; absent target signer
contents; exact isolated provider; protected state/health/lock paths; empty old
source group and inhibited restart paths. Refuse rather than initialize, resend,
guess a receipt, expand a budget or overwrite an incomplete attempt.

Capture original/included/final financial vectors before stopping the owned node.
Keep node and source/target keeper lifetimes in separate owned groups so stopping
a keeper cannot destroy chain evidence. Compare NFT/LP/rights and reserve vectors
at inclusion versus after unsigned recovery, not against a false assumption that
every paid harvest leaves pre-inclusion accounting unchanged. Stop all new groups
empty and compare original source/journal/config and unrelated host states.

This is an isolated restored-fork operating composition. Public current canonical
truth, real providers, physical second-host/OS recovery, durable disaster-domain
storage, external alerting, production signer fencing, sustained operation and
independent live adoption remain unqualified. The desktop heartbeat stays paused.
