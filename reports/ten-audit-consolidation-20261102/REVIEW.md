# Ten-report findings consolidation and improvements

Reviewed November 2, 2026, Europe/Paris, from main `9bd13df`.
**Production remains NOT APPROVED.** This expands the previous five-report
reconciliation to ten underlying technical findings narratives, using their
relevant verification records and current code. It does not count the previous
consolidation as another independent audit or repeat historical test totals.

## Reports and current disposition

| Technical findings file | Current conclusion |
| --- | --- |
| [November 2 improvement audit](../improvement-audit-20261102/REVIEW.md) | Custody-reader, current-cap admission, health/report and verification-tool repairs remain implemented. |
| [October 31 source/operating audit](../today-audit-20261031/REVIEW.md) | Reader publication, shared-infrastructure lineage admission, current fixtures and current static record remain implemented. |
| [Adaptable policy](../adaptable-policy-20261031/REVIEW.md) | Bounded future-only policy, scoped reviews and explicit source6 boundaries remain implemented; services are not qualified by configuration alone. |
| [Manual operations](../manual-operations-20261031/REVIEW.md) | One Operator manual, exact authority/input/recovery procedures and offline review hashing remain applicable. Historical callable/size counts stay historical. |
| [October 31 source changes](../day-audit-20261031/REVIEW.md) | Physical-read availability, actual activation binding and final active-main guards remain. Route-candidate viability remains open. |
| [Residual operations](../residual-operations-20261031/REVIEW.md) | Independent residual closure and main-preserving recovery remain implemented. Large attributed idle is not surplus or permission to bypass entry guards. |
| [Optional portfolio](../optional-portfolio-20261030/REVIEW.md) | Bounded two-leg custody, entrant-only growth, both-leg harvesting and near-eligibility observation enrollment remain. Source6 governed policies supersede source5 fixed labels. |
| [Complete-project audit](../comprehensive-popl-20261029/REVIEW.md) | Post-exit reserve-only venue recovery, identity/telemetry, chronology and evidence-admission fixes remain. Lifetime history/read-model scaling remains unfinished. |
| [Historical reconciliation completion](../historical-reconciliation-completion-20261029/REVIEW.md) | Strict CLI admission and preserved original provenance remain. Its 352-report/235-group inventory is historical upstream work, not newly executed here. Retired architecture is not reintroduced. |
| [Keeper coordination](../keeper-coordination-20261029/REVIEW.md) | In-range compound waits, reset acknowledgement, receipt-proved harvest clocks and actual-ABI reservation reads remain. Further independent harvest-identity checking is repaired below. |

Documentation-only synchronizations, passive-strategy research and the prior
five-report aggregate are not counted among the ten underlying campaigns.
The [75-group disposition matrix](findings.json) carries forward the earlier
41 groups and adds the material findings/limits from the other five reports.
There are 51 implemented-source groups, 5 superseded groups, 8 accepted
boundaries, 2 open implementation groups and 9 qualification groups. These are
overlapping review categories, not 75 separate bugs, new fixes or tests. Each
links current mechanisms and an existing central Todo owner.

## Implemented improvements

### Independent harvest geometry proof — medium diagnostic gap, repaired

The read-only maintenance report checked the main position's owner and PoolKey
but omitted the packed PositionInfo identity. For the residual, it decoded ticks
from PositionInfo and compared those same ticks back to that value. A coherent
PoolKey could therefore accompany malformed packed identity, impossible geometry
or a residual range inconsistent with the Manager, without the harvest report
rejecting that evidence.

`Review._harvest_ticks` now independently reads `Manager.ticks(lpId)` for each
actual leg, checks signed tick bounds, ordering and spacing, and compares it with
the packed PositionInfo using the existing reviewed identity validator. Both main
and residual use that proof. Current-owner, same-pool and liquidity checks remain;
existing known wrong-pool/owner blockers are retained rather than guessed valid.

This is **stored geometry**, not an active-range requirement. A one-sided,
out-of-range or filled residual can still be harvested. The proof needs no spot,
USD feed, swap quote or earned-fee estimate. Missing/contradictory stored geometry
makes that report unavailable; price-feed failure alone still need not do so.
The change adds at most one Manager getter per physical leg per bucket, within
the existing bounded report budget. Real latency remains unqualified.

The report now exposes validated main/per-leg ticks and explicit
`protocol_policy_version` metadata, distinguishing source6 Policy1 from historical
policy0. Five new regression methods are included in focused keeper selection.
They exercise profiles4/5/6, corrupted packed fields, Manager mismatch, impossible
geometry, both-leg success without market reads and source6 price-outage behavior.

No contract, keeper scheduling, signing, journal reconciliation, fee allocation,
LP operation, custody guarantee or financial setting changed. This is not proof
of an exploitable deployed contract; it corrects falsely permissive diagnostic
evidence. The normal contract harvest remains a separate independently guarded
call, and `ok:true` still only means the read-only report was produced.

### Current operating guidance and remaining work

The operator and keeper guides now explain the additional stored-identity reads,
what missing geometry means, and why price outages remain separate. Do not edit
a journal/configuration or weaken a guard to make the report green. Source
publication does not install a new reader or restart a worker.

The central Todo and roadmap now explicitly retain the lifetime-history issue:
complete event/block/lineage replay eventually meets finite work budgets. A
reviewed archival/checkpoint/read-model design needs integrity, reorg, lineage,
restart and retention verification; arbitrary limit increases or an unsigned
cached total are not a safe fix. No speculative accounting engine was added.

## Findings that remain open or accepted

- **Ordinary route-candidate viability:** final active-main guards safely reject
  an unusable placement, but bounded ranking may miss a viable alternative.
  The previous operator workaround is conditional, not an implemented solver fix.
- **Lifetime history scaling:** current correct bounded replay does not establish
  indefinite service availability. Preserve current exact evidence and limits
  while designing qualified archive/read-model evolution.
- **Real dependencies and operating qualification:** dual feeds, actual routes,
  RPC/VRF, authority addresses, OpenSea/storage, source6 website/services, maximum
  gas and real recovery/market rehearsal still need evidence. Synthetic token
  callbacks, old hybrid traces and chain-relabelled testnet fixtures cannot close
  those requirements.
- **Accepted trust:** direct governance and reviewed replacement code, explicitly
  bypassable paused emergency finances, upstream proxies, sampled evidence,
  cooperative rather than absolute socket timeouts, lost keys and rejecting
  external receivers retain their documented limitations.

Cooldown raw observations/paid enrollment and current source6 static review are
already implemented; old recommendations describing them as future work are
superseded. Outside-range no-swap compounding, automatic idle-only scheduling,
retired bridges/creator inboxes/Power/stablecoin entry and external custody drains
are not silently added. Current ETH/fixed-ZZZ, 80/10/5/5 and current-owner rights
remain authoritative.

## Evidence and completion boundary

[Verification](VERIFICATION.md) preserves original failures and scope. All 172
checked artifact entries match; 222 selected historical/previous-consolidation
files remain byte-identical. Historical source-pin inventories are not compared
to current code and falsely labeled current passes. All 83 current compiler-input
contents still match the exact normal policy6 build; unchanged Solidity gates
and static evidence are reused, not rerun to inflate counts.

The expanded report/matrix, Todo, feature reference, roadmap, release boundary,
current repository context and relevant operating instructions are synchronized.
No site/service, Anvil/NFT/LP/balance, transaction journal, public signing,
deployment/sealing or paused heartbeat changed. Independent release audit and
approval remain required.
