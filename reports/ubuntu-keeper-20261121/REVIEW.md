# Ubuntu preparation and focused keeper code review

21 November 2026. Production NOT APPROVED. Baseline
`a5570c95bbaba7472ba5370e43494b87246e0ea7`.

## Outcome and scope

Advance the missing Ubuntu stock-daemon/real encrypted Cast partition of
[Q06](../q06-keeper-recovery-20261117/REVIEW.md). The original inert-signer,
recovery-only evidence retains its original scope and is not rerun or relabeled.
The [execution plan](PLAN.md) defines the intended bounded new cases. The
operator then redirected work away from further rehearsal setup to direct code
inspection. Both new labs and all eight owned units are stopped, with zero
remaining cgroup processes. No live journal was initialized; no normal live
keeper or real Cast transaction ran. **The Ubuntu normal-daemon/signing/recovery
partition did not pass and remains open.** Preparation is not qualification.

The [read-only host inventory](inventory/REVIEW.md) confirms Ubuntu 24.04.3,
Python 3.12.3, systemd 255 and native Foundry 1.4.4. Existing staging Anvil was
already failed before this work; installed keeper was inactive. Existing nginx,
observer, sites, services, credentials and recovery journals remain outside the
rehearsal. No existing staging service is repaired or restarted.

## Isolation and evidence reuse

New root-owned lab directories and resource-bounded transient units use readonly
source/tool copies. Unprivileged cache, Anvil, proxy and keeper processes share
a new private network namespace; separate cgroups keep the chain alive across
keeper restart. Actual namespace identities and loaded process/unit settings
must be observed, not inferred from configuration alone.

The restored normal 39-instance F6/two-NFT graph comes from the source-bound
[Entry archive](../pool-integration-20261120/REVIEW.md). The existing 307-entry
fixed-anchor historical cache comes from the
[fee-flow archive](../pool-fees-20261121/REVIEW.md). No construction, Entry,
population, fee-economics, unchanged contract/browser or Python suite is rerun.
Fixture depth and correlated controlled prices remain synthetic. Only the
owned clock and controlled feed timestamps are aligned with Ubuntu UTC; their
answers remain unchanged. None of this qualifies live markets or Robinhood fees.

A new encrypted disposable signer is funded/authorized only on the owned fork.
No private key, password, encrypted keystore or raw signed payload is exported.
The worker must use the unchanged stock `python3 -m keeper.monitor --live`
entry point and real pinned Cast, with the existing 24M/full-25% maintenance
profile and hourly harvest interval. Optional jobs are explicitly disabled in
this finite fixture; it is not all-enabled P20 acceptance.

## Retained preparation failure

The first source-bound workspace installed successfully and generated its
disposable encrypted wallet. Its cache became ready, but Anvil startup failed
before bootstrap, signing or live-journal initialization. A bounded diagnostic
listener captured the exact request:

```json
{"method":"eth_chainId","id":0,"jsonrpc":"2.0"}
```

The original cache required an explicit `params` member. The
[JSON-RPC request specification](https://www.jsonrpc.org/specification#request_object)
allows omission. The report-only cache correction accepts exactly this
three-member zero-argument `eth_chainId` envelope, records its original shape and
wire hash, adds `[]`, then invokes the unchanged strict historical validator.
It does not convert IDs, accept null/batch/extra-field requests, fabricate
missing historical reads or add public fallback. Production code is unchanged.
The original inputs/failure and stopped-owned-unit result are retained. The
separately pinned retry started successfully, then exposed missing historical
fresh-wallet and keeper-mapping reads. Its interval-mining setup also hit a
receipt lookup before mining; Anvil attempted an upstream fallback which the
offline cache refused. No missing value or receipt was fabricated. Later bounded
read-only mapping responses are retained but were not adopted for another run.

## Direct production-code improvements

The follow-through fixes confirmed production Python issues rather than adding
more fixture construction:

- **Recovery intent:** `Keeper.submit` now validates a nonzero hash with the
  same existing parser as journal loading, before assigning it. A zero/malformed
  response retains the exact reloadable hashless intent and original fatal
  error behavior. It grants no permission to resend; successful mixed-case
  hashes normalize without changing the reviewed transaction or accounting.
- **Fee diagnostics:** profile2 captures one positive quote before simulation,
  using identical type2/max-fee/zero-tip fields for simulation, estimation and
  cost. Profile1's existing envelope/zero-price behavior remains unchanged.
- **Compound diagnostics:** an existing tracked observation is authenticated
  at the report's pinned block. A required clear is blocked; malformed/missing
  proof is unavailable. This is the existing keeper-only software policy,
  not a new contract restriction. Reporting never writes a reset, schedule or
  acknowledgement, and independent harvesting remains reportable.
- **Persistent lock:** keeper and indexer now pin a real protected direct
  parent, open with no-follow/nonblocking/close-on-exec flags, validate file
  type/owner/permissions and check named inode identity after flock. New locks
  are0600; safe existing0644 locks keep their bytes/inode/mode. No unlink or
  lock-file replacement is used. Trusted ancestors, the same UID and
  multi-host fencing remain host responsibilities.

## What actually passed

| Changed scope | New passing methods | Affected existing methods | Evidence |
| --- | ---: | ---: | --- |
| Nonzero signer hash and reload/no resend | 2 | 0 | [Red/green source-bound records](code-review-hash/GREEN.json); the new zero-hash method first failed on the original source |
| Profile2 fee envelope and tracked compound evidence | 4 | 3 | Seven-method current stage in [the exact public archive](EVIDENCE.json); four new methods first reproduced the old assertions, with no setup errors |
| Confirmation3 threshold-return branch | 1 | 0 | [Separate original console result](code-review/CONFIRMATION3_TOOL_RESULT.json); no rerun of the seven-method stage |
| Unix lock helper | 8 | 0 | Actual Ubuntu24.04/Python3.12 UID65534 execution in the public archive; temporary fixtures/children removed |
| **Distinct total** | **15** | **3** | **18 passes across explicit stages**, not one fresh full-suite run |

The separate confirmation3 method uses an accounting5 transcript, not an F6
runtime. The eight Unix methods exercise creation/legacy compatibility,
symlink/FIFO/permission rejection, contention and SIGKILL/reacquisition. The
other methods use inert signer/RPC fixtures. Red reproductions are not extra
passing methods. No unchanged contract/browser suite or population was rerun.

The [archive manifest](EVIDENCE.json) binds98 explicit public members including
original failures, fixed-block read provenance, source stages, independent
cleanup and host readbacks. Archive SHA-256:
`ba41f8f49d30b9f697842c214acc0f330d11ff82cee464591de6d1fbc0587553`.
The separate confirmation3 console receipt and hash red/green records are
retained alongside it without pretending they were original archive members.
After all eight units were confirmed stopped, only the four unused disposable
lab keystore/password files were removed. The [disposition metadata](verification/SECRET_DISPOSITION.json)
and execution record are separate supplements; their contents were never read,
hashed or exported. Existing SSH credentials and all public evidence remain.

The [current inventory](FUNCTION_INVENTORY.json) verifies179Python files and
1,980named definitions; the frozen F6 Solidity61/dependencies39/controls4 maps
and1,021ABI rows are unchanged. The normal verifier references this generated,
checked inventory. The three new test modules are registered in the maintained
keeper selection; inventory-only selection executes no tests. Todo generation
and the1,021-row operator reference check pass. Journal schemas, financial
limits, roles, contract runtimes and normal service defaults are unchanged.

## Source adoption and remaining code review

No running process uses these edits automatically. Review matching keeper/checker
source identity and follow the [operator procedure](../../docs/OPERATOR_MANUAL.md#keeper-lock-and-recovery-source-adoption)
before future adoption. Preserve existing journal/config/nonce/spend/receipts and
lock inode. No API/checkpoint codec is relabeled, and no website is published.

One resource-hardening item remains explicit: Cast address/send use30/90-second
timeouts with captured stdout/stderr but no byte ceiling. A future bounded
capture must preserve uncertain intent and never trigger an automatic resend.
This review establishes the missing limit, not an actual exploitable fund-loss
path. It is recorded in the sole Todo rather than inventing a new policy here.

## Uncompleted rehearsal criteria

Future separately reviewed execution still needs to establish:

- Clean final preflight with no cache miss, before live initialization.
- Actual normal-daemon signing and a durable hash while mining is held.
- Same-inode lock exclusion and keeper-only interruption/restart.
- Recovery of that exact hash without resend; canonical transaction, receipt,
  nonce, fee spend and authenticated harvest clock reconciled exactly once.
- A subsequent healthy normal cycle, local RPC failover, honest degraded health
  and recovery, then intentional stop without an unintended restart.
- All owned processes/units stopped and installed-service baseline preserved.

`Vault.collectFees` is permissionless under its lifecycle/custody guards. Its
receipt proves this signing/recovery journey, not privileged rebalance
authorization. Fresh signer-role admission is a separate check.

## Remaining release limits

Production keys/providers and complete fees, all enabled jobs, broader normal
scheduling, hashless uncertainty, off-host restore/fencing, disk-fault variants,
external alert delivery and sustained operation remain separate qualification.
No source publication deploys a service, signs publicly, seals contracts,
changes websites, resets existing Anvil state or resumes the user-paused
desktop heartbeat.
