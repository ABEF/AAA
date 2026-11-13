# Audit and improvements for the44linked unfinished tasks

13November2026. Baseline `53633b9854b5efea090a91388c3df0c04a5ca3e0`.
**Two production Python paths are corrected, optional probe pacing is implemented,
and current operator guidance is repaired. All44broad tasks retain open release
obligations. No financial policy, Solidity or live environment changed.**

## How the request was improved and executed

The [improved audit prompt](PROMPT.md) uses the exact44unique unfinished Todo
owners linked to the310historical records, rather than inventing44independent
bugs. It requires source/provenance inspection, distinguishes implementation
from qualification and accepted trust, prioritizes reachable failures and
recovery, and asks only consequential unresolved questions. Two critical prompt
reviews reject blanket closure, impossible universal guarantees and unnecessary
unchanged testing. Work follows that scope and preserves all established rights.

[Task assessments](TASK_ASSESSMENTS.json) cover every44owner with original finding
IDs and exact pointers into34contract,16backend and9keeper review views. These
views overlap; they are not59independent findings or freshly executed features.
The task-level review inspects concrete functions/controls and existing evidence,
not every line of every component as a new independent audit. Current statuses
remain exclusively in the [sole Todo](../../TODO.md).

## Confirmed fixes

| ID | Before | Correction and verified scope |
| --- | --- | --- |
| RPC44-01 | Probe checks continued using the same endpoint after HTTP401/403/429 or sanitized RPC-rate refusal. | Stop further transport to that endpoint, retain the original failed observation and continue separately configured endpoints. A refusal never counts as successful missing-block evidence. |
| RPC44-02 | A logical-call deadline could expire during its internal chain check, then permit the actual method POST. | Enforce the original90-second budget at each actual post and at the final clock-capture boundary. Keep100logical reads and an independent200post ceiling. |
| RPC44-03 | A later probe transport could retain its8-second timeout despite less remaining endpoint time. | Clamp to positive remaining time and restore the original timeout afterward. This does not preempt DNS/HTTPheaders or replace process supervision. |
| RPC44-04 | The passing network study needed a one-off paced transport wrapper. | Current CLI accepts optional exact integer `--request-interval-ms 0..5000`, default0 unchanged. Pacing covers actualHTTP starts, including chain checks, and consumes the same90seconds.13new methods pass; no new public profile or cadence approval. |
| BE44-01 | Any log-fetch RpcError caused smaller-range attempts, including wrong-chain, expired-work, rate/auth, missing-block, invalid/protocol and transport failures. | Indexer stops adaptive shrinking for these known global/terminal faults, including exact local malformed/redirect/deadline diagnostics. Opaque size/range errors, the genuine response-size ceiling and HTTP413retain bounded adaptation.7new methods verify refusal and healthy reduction. Shared transport retries and normal polling are separate. |
| DOC44-01 | Operator table forbade all spot sources despite the approved reviewed spot-composite design. | Permit explicitly reviewed spot sources while retaining two-source/freshness/agreement/runtime and execution controls; no unreviewed target-pool or$1fallback. |
| DOC44-02 | Some current setup prose called LP2/schema15 mandatory and deployment text retained schema14. | Distinguish current schema17 and explicit execution-price1/LP3 from historical omission0/LP2, exact constructor/runtime/helper bindings and separate keeper/inventory versions. Historical reports/profiles remain immutable. |

Probe code changes only `keeper/probe.py`; the generic Rpc and keeper monitor,
health-source fingerprint and saved fee/nonce/pending state remain unchanged.
Indexer changes only failure scheduling in `indexer/monitor.py`; canonical log,
ancestry, confirmation, chronology and transaction-write barriers remain. A
refused fetch causes no new ingestion/cursor advance. A legitimate `reconcile()`
reorg rollback can already have occurred earlier in that step; do not promise
an unchanged database on every failed step.

The specialized keeper runner now registers the new probe test module. General
discovery already selects the new indexer module. Inventory-only checks execute
zero methods, not an unchanged regression suite.

## Contract, accounting and operational conclusions

The inspected source preserves entrant-only main growth, both-leg ownership and
NAV, fixed80/10/5/5, exact-unit/current-owner LP and royalty rights, terminal
governance distribution, separate reserves, typed callbacks and atomic rollback.
No reproducible new Solidity exploit was established in this task-level review;
that is not proof of exploit absence. All61production Solidity files and their
accepted100-source normal closure remain byte-identical, so compiler/static/EVM
evidence is reused only within its original source scope. Oracle3-byte/Vault32-byte
headroom remains a release constraint, not solved by these Python changes.

Raw ZZZ LP-reward recovery, original-currency royalties, residual close into
attributed idle and governance emergency loss bypass are intentional distinct
paths. Do not delete them as obsolete or silently change their economics.
Compounding's in-range/below-threshold wait remains service policy selected by
the user; a compromised authorized keeper is not constrained by that off-chain
choice. Repeated permitted losses, spot manipulation and emergency governance
trust remain explicit risks. No cumulative-loss/TWAP/24-hour policy was added.

The late-fee-credit concern remains dependency-qualified: a malicious reachable
callback after the final harvest could affect increase accounting, but ordinary
swaps cannot interleave inside one transaction. Actual fixed-token/Permit2/
periphery behavior and controller reachability must establish an effect before
adding a speculative debit guard or claiming a demonstrated exploit. Existing
actual dependency review remains required.

## Remaining work and required inputs

| Remaining group | Exact next requirement |
| --- | --- |
| ETH/ZZZ sources and execution | Two healthy genuinely independent valuation paths, publication/round/age/liveness/control review and meaningful compatible bidirectional depth. The latest retained market failures are not refreshed or turned into approval. No automatic destination/source/route change. |
| Gas, provider and deployment | Numerical full20M/24M work capacity/plan/SLA/archive, exact current mint2/4663 operations and complete Nitro fees, approved transaction/day/funding bounds, actual constructor arguments and size/gas. Old synthetic profiles do not supply these. |
| Authority/OpenSea/VRF/artwork | Operator-selected real public authorities, actual marketplace onboarding/fees/payers/stages, funded proof-verifying randomness and original-request recovery, independently verified publication/CID/pinning/retrieval. No address, account, subscription or approval is invented. |
| Claims/history/maximum state | Actual royalty/LP token behavior and liveness, currency/cohort/claim/canonical workload, current-price history/checkpoint/lineage/raw archive/restore. Allocated exact units do not make frozen tokens transferable or eliminate explicit unallocated cohorts/upstream fee carry. |
| Maintenance/custody/recovery | Real one/two-position operations, post-close depth and economics, same-pair capacity/cutover, canonical/escrow compatibility, isolated holder payout failures, signer fencing, Linux supervision, backups/host/key loss and off-host monitoring. |
| Frontend and release | Actual current-profile deployment/API/provider/wallet/hosting acceptance and separately authorized rollout; independent audit/remediation and final sign-off. Source9/10 remain unsigned; public configurations remain null. |

No new unresolved economic/authority/strategy choice was required for the
confirmed fixes. Existing selected policies remain intact. Required external
inputs and separate operating authorizations are explicit above; their absence
is not something a code patch or mock can repair. The44linked tasks remain
unfinished broad workstreams; the full ledger still has47unfinished tasks.

## Verification, preservation and publication

**20distinct new regression methods** pass across explicit recorded source
stages:13probe and7indexer. Baseline failures, an unsuccessful local edit-harness
attempt, a corrected draft scenario and final boundary reviews are retained.
Counts overlap across intermediate runs and are not added. See
[verification](VERIFICATION.md), [probe evidence](keeper-rpc/REVIEW.md),
[indexer stage map](backend/VERIFICATION_SCOPE.json) and
[read-only peer review](contracts/PEER_REVIEW.json).

Current Todo/operator/reference/link and exact source-publication checks are
recorded in the [completion receipt](COMPLETION.json). Original current docs were
archived first; no historical report is rewritten except its navigation index.
The4protected dirty files and unrelated drafts stay untouched/unstaged. No
public RPC probe, financial operation, signature, deployment, service/site,
existing Anvil/NFT/LP/balance/journal or user-paused heartbeat change occurred.
Main-only source/docs publication is not operating or production approval.
