# Ubuntu recovery and operating-feature qualification — 24 November 2026

## Scope and preservation

This follow-through addresses the failed full Anvil export/reload and inventories
33 Ubuntu-bound operating partitions. It separates new execution, source-exact
reuse, expected refusals and unqualified work. It does not promise every market,
workload or fault combination has been dynamically tested.

The starting revision is `064cd93060b626b885cf88772fa2eb959d51c706`.
Fresh private-network labs use copied inputs, bounded resources and disposable
local signing only. No public transactions, new sealing, installed-service/site
rollout, existing Anvil reset or heartbeat restart is authorized or performed.
The frozen F6 Solidity/dependency/control maps remain 61/39/4 and 1,021 ABI rows.

## Complete snapshot recovery

The operator explicitly approved a **new isolated snapshot profile**: 32 MiB
HTTP/capture response only for exact `anvil_dumpState([true])`, unchanged 16 MiB
compressed data, and 128 MiB expanded JSON. Every other response retains 16 MiB;
request, time, request-count and resource limits remain. This is report tooling,
not a production API/keeper configuration or a general response-cap increase.

The c7e9 attempt read the complete response but still failed at its original
capture layer. That failure is retained. c7eb corrects the matching capture
boundary and replaces a large repeated-group hex regex with strict bounded hex
decoding, including whitespace refusal and decoded-length equality. Nine NEW
offline methods pass; they do not execute Node or an old test body.

The [actual reload receipt](evidence/snapshot-reload.json) records a complete
12,805,401-byte compressed / 47,369,005-byte expanded snapshot. A new node reloads
all 45 headers, 44 transaction receipts, 39 runtimes, 112 bindings, nonce/balance
and genuine NFT-contract parent/creation/latest-code proof. Forty-four historical
snapshots are retained. A separately fetched private gzip matches independently
on Windows: [integrity review](evidence/snapshot-local-integrity.json).

This is the new unsealed constructor-double fixture. It is neither recovery of
the exact original c7e6 timestamps nor the separate sealed F6 graph's missing
historical creation proof. Original failed exports and checkpoint/DB/journal
bytes remain unchanged. Raw snapshots, keystores, passwords and journals are not
published.

## Confirmed implementation corrections

| Correction | Result | New verification |
| --- | --- | --- |
| Keeper preflight omitted reciprocal LP routing validation | LP1/2/3 no-pending preflight uses the normal routing observer and reports `lp_routing`; saved pending recovery acquires no new dependency | One NEW baseline fails before correction; four NEW methods pass, including wrong parent, sanitized fault and pending independence |
| Successful pending recovery unnecessarily doubled the next normal wait | Health stays degraded until fresh checks; refresh-only recovery uses normal cadence after earlier sample/jitter deadlines; real errors/reverts retain backoff | Ten distinct NEW methods pass in explicit 7+3 stages; the first seven bodies are not rerun after the deadline-order correction |

Both Python changes enter keeper health source identity. Adopt a matching writer
and checker under the existing fenced recovery procedure; do not edit journals
or source hashes. These two modules are not checkpoint semantic sources, so the
fixes alone do not require a checkpoint rebuild. No financial rights, journal
schema, public signing capability or default limit changes.

The future-only staging installer now extracts reviewed Foundry binaries with
`--no-same-owner` and verifies regular, nonsymlink, single-link root ownership
before setting executable permissions or executing a tool. Root extraction
previously preserved the archive builder's UID/GID. No installed binary is
chowned, replaced or automatically adopted by this source correction.

## Actual stock keeper, diagnostics and indexer

The c7ed partition runs the actual `python -m keeper.monitor` daemon and real
encrypted Cast signing with interval 240 seconds, 12 confirmations, hourly
harvest, and unchanged 24M/full-25% maintenance and fee/spend bounds. It verifies
39 runtimes and all 91 static bindings, initializes a fresh journal, submits one
harvest, rejects a lock contender without mutation, stops with the saved hash,
mines confirmation blocks, restarts the same journal and reaches a fresh
`healthy_v2` normal cycle.

Transaction `0x0909e373970398caf90df6f89cafc74600cae88f40d0c25f7b6810be929ecc24`
uses 300,814 gas. The independently checked receipt charge is exactly
300,814,033,089,540 wei; nonce goes 0→1, pending clears and no second submission
occurs. These are local model fees, not Robinhood fee qualification.

Five real `keeper.ops` CLI commands pass: preflight, simulated operation review,
health, snapshot and snapshot verification. The actual indexer ingests the local
harvest log, restarts its database and replaces two confirmed **empty** headers
under a controlled 13-block branch change, keeping the actor receipt/journal.
This does not prove deletion/replay of orphaned financial logs.

History backup, verify, restore and a bad-manifest refusal pass on new copies of
the current-semantic source9/V9 synthetic history. The entire c7ed aggregate
remains `success:false`: its later private negative-import fixture incorrectly
expected a shorter-prefix error from a standalone graph that has no lineage.
The successful earlier partitions are separately authenticated; the aggregate
failure is retained and is not relabeled as a complete pass.

## Exact history import and restore

Fresh current-semantic checkpoint preparation covers preserved synthetic history
for 1,000 NFTs/900 active and three epochs without regenerating logs or rerunning
wallet journeys. Windows builds a new schema2 prefix at block46 and imports it
into three epochs at161. Ubuntu separately builds a two-epoch schema3 prefix and
exercises the distinct schema3 two→three import branch. Positive CLI entries use
explicit fixture-injected lifecycle/getter observations: this proves current
SQL/replay/import mechanics, not F6 EVM or provider history.

The original comparison stops remain. The Ubuntu candidate differs in exactly
six provenance fields: active161 and completed140 history now name the new
schema3 prefix and zero extra suffix logs. A read-only recursive probe finds no
other difference. c7f2 derives these values from the pinned prefix and the
authenticated first handoff, then requires whole decoded-state equality,
including nonzero exact-LP high/low phase. Neither successful importer is rerun;
c7ee's original aggregate remains `success:false`.

The continuation executes only the four unfinished backup, verification,
exclusive restore and restored-verification CLI calls. All pass in 3.924 seconds;
raw tables, checkpoint/review bytes and the full 86,400-second window match.
Prior source/artifacts stay unchanged and the owned process group is empty.
The standalone negative importer also refuses without publishing artifacts.
Checkpoints remain uninstalled. See [source/evidence reconciliation](HISTORY_RECONCILIATION.json).

An initial Windows `mode=ro` inspection of preserved WAL databases created empty
WAL/SHM sidecars. Only those proven-new sidecars were removed after verifying the
unchanged database hashes and original absence. Subsequent SQL reads use new
writable copies or `immutable=1`; original DB/checkpoint bytes and sidecar absence
are verified. This filesystem side effect is not hidden as a no-touch read.

## Remaining keeper jobs and observed blockers

| Feature | Actual new observation | Limit of the result |
| --- | --- | --- |
| Metadata | Real Cast batch, two authenticated NFT IDs, canonical receipt and suppression of unchanged repeat | Two active NFTs; not every lifecycle/marketplace/load state |
| Retired workers | Exact rejection of fresh royalty conversion, keeper principal distribution and adaptive-range configuration | Correct refusal; no removed feature is re-enabled |
| Compound | Real fee-generating swaps/harvest and stock preparation reach `cost_cap_exceeded` | No compound broadcast; unchanged0.01ETH maximum-cost ceiling remains |
| ZZZ burn | Controlled real fee reserve exists but copied `totalSupply()` reads0 | Missing uncached global state; not proof of actual token supply or successful burn |
| Normal confirmation | Four genuine observations at1795543607/3847/4087/4208; gaps240/240/121s; maturity600s and LAST_OBSERVED146s jitter | Lab-wide6,000-request ceiling stops before ordinary replacement. Terminal read failure invalidates scheduling by source rules; no final-current schedule or completed rebalance is asserted |
| LP conversion | Actual typed Slippage refusal at11,010ppm directional fee against preserved100bps cap; original NFT credits unchanged | No positive conversion or cheaper-route qualification |
| Operator width change | Only5000→2500 changes; pending geometry and jitter progress | Replacement stops at unchanged0.01ETH maximum-cost ceiling |

These are controlled copied-state/direct stock-method partitions, not continuous
wallclock daemon operation. All stronger financial/source/callback/ownership
guards remain. See [LP keeper reconciliation](LP_KEEPER_RECONCILIATION.json) for
exact source, receipts, clocks and byte-identical harness sources. The6,000-request
ceiling is this multi-cycle lab's work budget, not a newly introduced production
keeper limit. No budget is raised or estimate replaced with receipt gas to pass.

The c7f6 permission trial correctly clears observations under pause and stops
the worker after key revocation, but its later contract assertion uses the wrong
endpoint: `collectFees` is permissionless while live. Its false aggregate stays.
The separate RPC-fault partition passes six injected read failures, preserving
pre-send nonce/no submission and exact post-send pending bytes/same hash/no resend.
Permissionless collection gives the caller no fees, principal or configuration
rights. Ordinary `rebalance` remains `onlyKeeper`; permission changes are neither
necessary nor authorized to make a mistaken test pass.

The c7f8 continuation executes only the missing correct authorization checks and
restored harvest. Revocation makes `rebalance` return typed `Unauthorized`;
permissionless `collectFees` simulation succeeds without changing checked state.
Restoring the same key permits one actual Cast harvest, with the authenticated
receipt and no gateway errors. Different-key rotation and off-host fencing remain
unqualified. See [authority/recovery reconciliation](AUTHORITY_RECOVERY_RECONCILIATION.json).

## Future installer and command surfaces

An actual GNUtar demonstration with one nonexecuted synthetic archive member
reproduces UID/GID1001 preservation and verifies `--no-same-owner` yields root
ownership. Five actual shell parser checks pass. c7ef then encounters an OS
`PermissionError` before its first unprivileged help command; its aggregate stays
false and the exact OS cause is not established. A separately unprivileged c7f1
continuation completes only the 16 unfinished CLI help checks. No successful
tar/parser command is repeated. Help/syntax admission is not financial-feature
execution, a deployment rehearsal or permission to run an installer/observer.

The final installer also separates `test -f` and `test ! -L`: Bash `set -e` did
not stop on the left side of the earlier `&&` expression. A NEW FIFO baseline
demonstrates that issue; five NEW corrected cases reject FIFO/directory/symlink/
hardlink and admit a valid regular file. The exact extracted source fragment uses
a chmod sentinel, so no fixture permissions change. No tar/help case is rerun.

## Evidence boundaries

The copied sealed operating fixture is a **controlled latest-state model**.
Uncached original Robinhood state, original archive history, independent market
prices, external liquidity, complete fees and production-provider behavior are
not supplied by loading that state. Controlled feed timestamps/answers, synthetic
depth and local roles are labeled at their individual stages.

The first c7ea run refused before signing because its constructor manifest
expected a nonzero `bootstrap()`. `seal()` deliberately clears it. The retry
retains all 91 static checks with an explicit sealed-zero expectation and records
the original constructor expectation; it drops no binding check.

Operating bundles retain the starting revision plus their recorded exact
`keeper/ops.py` and `keeper/monitor.py` overrides. The final installer correction
has separate source-fragment verification; it was not installed into an existing
environment or retrospectively applied to an earlier receipt. The reproduction
manifest binds each published helper to its executed archive member. Private
transport, signing material, databases and raw state remain excluded.

All 16 new campaign units and process groups are stopped. The final read-only
comparison preserves all five original service states and the seven previously
stopped labs; its only ignored ambient change is the documented pre-existing
observer invocation. See [campaign cleanup](evidence/all-campaign-units-stopped.json)
and [host preservation](evidence/host-preservation.json). The user-paused heartbeat
remains paused.

## Remaining approval boundaries

Actual market/feed/route independence and depth, provider/complete fees,
production authorities, OpenSea custom Merkle compatibility, live randomness,
complete F6/V10 consumer history, maximum workloads, off-host restore/fencing,
alerts, sustained operation and independent approval remain separate gates.
Source publication does not adopt a runtime configuration or start a service.
The immediate remaining operating proofs are a completed ordinary replacement,
positive compound/geometry execution within the unchanged fee ceiling, complete
token state for burn, and an admitted cheaper route for the 1% conversion limit.
The [33-partition coverage](COVERAGE.md) keeps these separate from successful
snapshot, recovery, diagnostics, metadata and history evidence.
