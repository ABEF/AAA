# Action composition, volatility and outage review

Reviewed2November2026 against base main `8240de0`. Internal audit and implemented
mitigations; production remains NOT APPROVED. [Action/output matrix](ACTION_MATRIX.md)
and [verification](VERIFICATION.md) distinguish reviewed behavior, fresh tests,
unchanged contract evidence and unresolved qualification. No claim that every
possible upstream/market failure is eliminated.

## Reproduced defects and fixes

| Finding | Actual failure | Implemented change |
| --- | --- | --- |
| RPC body progress could outlast an attempt budget. | One buffered `read(n)` could wait over repeated timely socket fragments; no attempt elapsed-time or request-budget check ran until the whole body returned. Deterministic timed-stream regressions reproduce this. | [Read-only RPC](../../zzz_ops/rpc.py) reads available bounded fragments with `read1`, checks monotonic attempt time and request work before/after each fragment, retains the8MiB response limit, closes the response and preserves bounded failover/WorkLimit behavior. |
| Unknown maintenance settings were ignored. | Both global defaults and bucket overrides accepted misspelled intervals and unsupported `rebalance:false`, creating a false impression of changed operation. | [Keeper](../../keeper/monitor.py) requires the exact supported maintenance keys before new work. The diagnostic does not echo unknown names/values. No new rebalance-stop setting is invented. |
| New maintenance values could obstruct paid-transaction recovery. | A string boolean in new maintenance configuration prevented construction of a keeper with a valid saved pending intent. | Defer maintenance-value/unknown-key validation only while restoring an existing validated intent. Recover its exact receipt/nonce/cost first; strict validation then halts before any new work. Deployment, sender, contract, fee, receipt and journal identity checks remain. Malformed structural configuration is still rejected. |

The recovery change is not a configuration fallback: it authorizes no new job,
changes no saved transaction, and never treats an unknown setting as effective.
After the original receipt is confirmed, the operator corrects the configuration
and restarts with the same journal/nonce checkpoint. Other malformed deployment,
signer or job configuration may still require restoring the original reviewed
config before recovery; no global skip of security checks was added.

The transport fix uses the documented Python3.11 buffered-stream interface:
[`read1`](https://docs.python.org/3.11/library/io.html#io.BufferedIOBase.read1)
allows application checks between raw read steps, unlike a full buffered read.
[HTTPResponse](https://docs.python.org/3.11/library/http.client.html#httpresponse-objects)
implements that reader interface. This mitigates body dribbling; it does not
preempt DNS, stalled headers/chunk metadata or a single blocked socket read.
API child workers retain a separate hard30-second supervisor; keeper progress
watchdog and actual provider/TLS/OS behavior still need operating qualification.

## Action composition and volatility findings

The current contract path remains unchanged: entrants checkpoint incumbents,
spend only their own budget, increase the main and buy aggregate NAV shares.
Both actual LP legs are harvested, valued and closed together for a whole
adjustment. Residual disable is desired state until merge succeeds. The earlier
[six-day study](../portfolio-long-horizon-20261102/REVIEW.md) and
[actual-core routing repair](../lp-lifecycle-audit-20261102/REVIEW.md) retain exact
source applicability; their executions were not repeated as a fresh full suite.

New source6 fault transcripts confirm a one-minute price-condition failure drops
persisted jitter and requires reset recovery across restart. A fast market-side
reversal or restored opposite-side reference cannot reuse mature old evidence.
These are synthetic pinned-RPC transcript tests, not uninterrupted price proof.

Affected API/worker checks confirm partial USD failure can preserve ownership and
raw funded claims while exposing valuation as unavailable, reject malformed or
omitted LP legs, bound admission and terminate blocked child work. A read outage
does not turn a confirmed on-chain action into a failed transaction. Never clear
its saved hash, send another transaction or fabricate a zero to make the UI move.

The output matrix explicitly separates transaction status, operation events and
the economic post-state. For example, `Compounded` reports reserve release, not
the total actual LP increase when older idle is reinvested; `FeesCollected` is not
an individual NFT payout, and conversion/import/claims are not new income.

## Long-term operating policy and limits

- **Rapid price movement:** keep fresh independent price checks, actual quotes
  after withdrawal, active-main proof and captured execution budgets. If no safe
  candidate exists, retain the old portfolio atomically; do not automate the
  paused governance emergency as fallback. No profitable strategy or MEV immunity.
- **Hard12-hour minimum:** it can intentionally leave LP inactive during volatility.
  The600-second sampled window/300-second maximum gap/240-second checks and jitter
  can restart after faults. Preserve this chosen policy; report inactivity and
  exact blockers rather than silently shortening the interval or weakening guards.
- **Brief outages:** price-dependent work waits; independently healthy funded
  claims/allowed harvesting retain their own paths. An observed fault invalidates
  ordinary evidence even if price recovers before the next transaction. Unseen
  between-sample moves cannot be detected by this design.
- **Slow or failed services:** failover is bounded and same-block identity still
  matters. API worker containment is not keeper uptime qualification. Preserve
  pending records and use matching source/config, external progress/backup
  monitoring and controlled restart. The user-paused heartbeat stays paused.
- **Token/venue failure:** immutable approved identities and raw recovery limits
  do not make an upstream blacklist, pause, broken transfer or unusable pool
  recoverable in every case. Atomic both-asset movement may remain blocked.
  No arbitrary executor, recipient or principal sweep is added to escape that risk.
- **Economics and history:** per-operation caps do not cap cumulative turnover
  loss.5USD growth/hourly work needs actual gas qualification. ETH conversion can
  wait for a qualifying cheap route; never label unconverted ZZZ as ETH. Lifetime
  authenticated history still needs measured archive/read-model design before
  replay budgets are exceeded; unsigned cached totals are not a substitute.

Real dual feeds/routes/VRF/authorities, source6 website/services, OpenSea,
populated1000-NFT gas/load, Unix storage/ownership/backup/watchdog/reorg rehearsals
and independent audit/remediation remain open in the [sole Todo](../../TODO.md).

## Verification and preservation

176 distinct successful selected Python methods across recorded attempts; one
Unix ownership/permission method remains skipped. Original defect controls, one
corrected pending fixture, Windows test-driver failures and narrow corrections
are retained. The focused runner includes the new9 regression methods with strict
inventory membership. Inventory listing executes zero methods.

No Solidity production file, ABI, policy, role, custody guarantee, loss/timing
default or economic right changed. Reuse43 normal gates/475-record internal
static disposition only at matching52-source/31-dependency pins. No deployment,
sealing, public transaction, service/site/Anvil reset, journal/signer adoption or
heartbeat change was performed.
