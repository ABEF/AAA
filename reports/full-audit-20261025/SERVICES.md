# Services, integration and operating-boundary audit

## Scope and limits

This slice reviews the current committed candidate at initial main `e32e966`,
including the preceding `fbf31c6` native-royalty custody corrections. The current
source profile is accounting3/local Position, direct governance2 and same-chain
canonical V4. Historical profiles remain explicit. It does not claim that old
Anvil deployments, journals or the website's native-V2 reader became current-V3.

The review follows confirmed RPC reads through projections, transaction/activation
preparation, typed ABI/trace validation, bounded HTTP admission/isolated workers,
raw-log ingestion/history, keeper planning/signing/recovery and release preflight.
Website consumers were inspected read-only. The exact inspected file bindings
are in [the manifest](services-bindings.json); a hash is a scope marker, not proof
that every possible path in a file was executed or formally verified.

No production Solidity, existing SQLite/journal, website source/build/server,
Anvil/NFT/LP/balance, signing policy, service or monitor was changed here. The
offline tests use disposable temporary SQLite and synthetic byte-level RPC/trace
responses. Actual HTTP/RPC providers, browser extensions and deployment operation
remain independently unqualified. **Production NOT APPROVED.**

## Confirmed issues and implemented fixes

### S-P2-1: current dormant state was rejected by activation preparation

**High confidence, functional availability defect.** `ZZZVault.nftStatus` returns
the local `Dormant=3` for a minted NFT without a bucket. `Projection` already
derives `dormant_status=3` for accounting3 and 5 for historical profiles, but
`ActivationTransactions.prepare` still required literal5. A valid current NFT
could not obtain an unsigned activation review. The active growth code1 was
unchanged; this was not an on-chain loss or authorization bypass.

The preparer now uses the validated Projection's `dormant_status`. There is no
guess from response size and no fallback accepting both codes. A current5 or
historical3 status still rejects, as do outbound/parked activations and dormant
growth attempts.

### S-P2-2: current source-policy check could not encode native ETH

**High confidence, functional availability defect.** The current LP-only source
policy requires the preparer to read `isContributionAsset(address)` for both
native ETH and fixed ZZZ. The generic address encoder rejects zero addresses,
and `Projection._call` had not admitted the zero currency for this one predicate.
Thus current activation/growth still failed before approval/LP simulation after
passing the status gate. A growth case independently exposed this second failure.

Only argument0 of `isContributionAsset(address)` is now a typed native slot in
accounting2/3, matching its actual contract ABI. Zero contract targets, ownership
addresses and unreviewed address-bearing selectors stay rejected. Historical
profile1 remains outside the native slot extension. No raw call endpoint,
financial writer or signature permission was added.

The combined [original failure](activation-profile-before.json) selects five new
methods: six subcase errors exercise the two real production causes, while the
historical-profile2 preparation control already passes. The unchanged fixture
and assertions [pass after the fix](activation-profile-after.json): current
native activation into existing/new shared LP, current active growth, exact ZZZ
approval before re-review, typed zero-address boundaries and explicit historical
status separation. Native prepared contributions run both bounded trace phases;
the approval case emits no claim of LP deployment and starts no trace.

### S-P2-3: independent-history audit rejected the real RPC adapter

**High confidence, qualification-tool availability defect.** `Rpc.call` deliberately
returns a checked integer for `eth_chainId`, but `HistoryAudit.run` passed it to
the hex-string-only history quantity decoder. Every actual adapter invocation
failed before comparing the index. The earlier test transport returned wire hex,
so those tests did not represent the real adapter composition. No mismatched
history was falsely accepted; the tool failed closed but was unusable.

The audit now accepts an exact checked integer, or a canonical wire quantity from
an explicitly injected read adapter. Boolean/float coercion and noncanonical,
negative or wrong-chain identities remain rejected. The test uses actual
`Rpc.call` and its chain-check/normalization path, replacing HTTP I/O only.
Temporary real SQLite contents remain identical before/after every audit.

[Original composition](history-transport-before.json): the actual-adapter positive
case errors; the wire-quantity control and two negative methods pass.
[Corrected composition](history-transport-after.json): four of four pass. This
does not contact or qualify a real second provider, prove independence or log
completeness, or repair an existing index.

## Fresh verification and exact evidence boundary

| Selection | Result | Meaning |
| --- | --- | --- |
| Five new current/historical activation methods | 5/5 pass, 4.391s | Full offline current3/fee1/routing2/pricing2/review1 preparation composition; no altered fixture/assertion between before/after. |
| Four new history transport methods | 4/4 pass, 0.672s | Real Rpc adapter normalization, canonical injected wire compatibility, malformed/wrong-chain rejection and unchanged temporary SQLite. |
| Two existing directly affected controls | 2/2 pass, 0.938s | Historical profile1 selector/response and typed native/unknown zero-address behavior. [Record](services-compatibility.json). |

Total **11 distinct methods**, nine new and two existing, across the indicated
scopes. Before/after invocations and subcases do not add distinct coverage. No
unchanged broad Python, Solidity, fork, gas, browser or operating suite was rerun
in this slice. Final changed-code hashes and frozen test identities are retained
in the records. Root's final manifest/verification covers any later shared work.

## Wider reviewed boundaries

| Boundary and inspected implementation | Assessment |
| --- | --- |
| `server.py`, `activation_server.py`, `http_runtime.py`, `admission.py` | Exact loopback Host/framing/content-type/length handling; bounded headers/body/connection deadline and finite connections; only reviewed proxy origin/client identity; expensive work admitted after ingress. Client identity is capacity control, not wallet authentication. GET/unsigned preparation cannot sign. No new bypass confirmed in inspected paths. Public edge/proxy configuration and capacity are still operator qualification. |
| `worker.py`, `work_budget.py` | Fresh isolated worker per request, no shared Projection budget/cache across users; finite leases, deadlines, post-result freshness, terminate/kill/reap and quarantine on failed cleanup. A stuck child cannot silently become an available worker. Actual OS/process-limit behavior remains a deployment rehearsal, not proven by these read traces. |
| `rpc.py`, Projection `_snapshot/_verify_deployment/_finish` | Read-only method allowlist; bounded responses/retries and no redirect; checked chain per request; EIP-1898 canonical block pin, deployment anchor/runtime/module/lifecycle/profile and final freshness/confirmation checks. Provider agreement is still trusted observation. No fallback to latest/zero on pinned read failure. The discovered chain-representation mismatch is fixed only in the consumer. |
| `transactions.py`, `activation_config.py`, `activation.py`, `activation_trace.py`, `activation_v4.py` | Fixed typed operations and destinations, current owner/identity checks, exact contribution approval rather than unlimited allowance, no state override, actual trace phases/new LP measurement, captured caller cap, same-snapshot economics and separate gas. Reviews expire; they are neither reservation nor authority to submit. Unsupported dependencies and stale/mismatched traces fail closed. The two current-profile gaps above are corrected. Actual source/route/feed/provider qualification remains open. |
| `liquidity_context.py`, `price_policy.py`, earnings prices/portfolio/collection | Current status consumers use explicit profile mappings. Range warning timing is eligibility, not a promised keeper execution. Financial raw units remain exact; missing prices or custody valuation become unavailable, not fabricated zero. All chunks must bind the same inventory/block before total display. Actual oracle source independence and range-policy configuration remain review dependencies. |
| `indexer/monitor.py`, history/history-audit/earnings/lineage | Confirmed contiguous ancestry, bounded reorg proof before destructive writes, emitter/hash/index/transaction consistency before atomic insertion, raw replay rather than cached decoded labels, bounded read-only SQLite and complete cutoffs. Existing database trust and provider log completeness are explicit; the history audit compares one bounded window only. Native royalty exit/full-return events now replay without new income under the preceding source fix. No additional false-income path confirmed in inspected code. |
| `keeper/monitor.py`, `royalties.py`, `ops.py`, `state.py`, fee helpers | Default dry run; explicit live review and supported Unix ownership/locking; immutable code/profile checks; durable intent and captured fees before external signer; one serial nonce, ambiguity preserved, no automatic resend; canonical receipt/cost checks before checkpoint; bounded action/cycle budgets and cooldowns; backups exclude key/config contents. Old journal identity is not relabeled. Multi-host fencing, actual keystore/gas/provider operation and independent off-host alerts remain operator obligations. |
| `production_v2.py`, `production_observer.py`, holder preflight | Current accounting3/direct governance2/helper/runtime/source policy inventories are explicit. Observation and approved review evidence remain separate; missing actual reads cannot substitute declared values. OpenSea primary-mint compatibility is deliberately blocked. No arbitrary request can make a manifest authorize deployment. Existing evidence is not an independent audit. |
| Website `deployment-config.js`, `deployment-native.js`, `deployment-api.js`, `deployment-session.js`, `deployment-view.js`, `browser-wallet.js` | Public DEPLOYMENT is null; BrowserWallet requires chain31337; current native reader explicitly accepts accounting2, not3. Therefore current3 website support remains an **open incompatibility gate**, not silently enabled by this backend fix. No signer extension or website change was made. Session revisions invalidate account changes; typed review/independent receipt checks remain separate from display. Actual current-profile/wallet/browser operation still needs acceptance. |

A scan of other status consumers found no further unconditional dormant5 in the
current preparer/reader/keeper paths: Projection and collection use the explicit
mapping, and keeper uses `decode_position/status_name`. Legacy status tables and
old-profile fixtures retain their original meaning. Other real `eth_chainId`
consumers use the checked integer or an explicit adapter normalizer; only the
history-audit mismatch above was confirmed in the inspected set.

## Operator and release consequences

Deploying a reviewed compatible read/prepare release is still an explicit future
operating action. These source fixes do not update running services, existing
databases, Anvil, browser manifests or journals. Preserve those originals and
their configured profiles. Do not enable a current3 manifest through the older
native2 website validator or reinterpret a3status as historical remote custody.

For the separate-provider history audit, retain the existing independently
reviewed endpoint policy, canonical anchors, read-only SQLite and exclusive new
output path. A matched window is provider agreement for that window, not a
complete history/finality proof or automatic repair authorization. The fix merely
makes the actual checked adapter usable.

Remaining release work includes actual independent feeds/routes/VRF/authorities,
OpenSea primary integration, current3 website/API/provider acceptance, complete
logs/lineage and pricing, sustained Linux keeper/indexer operation and recovery,
strategy/max-state gas economics, actual capacity and independent audit. No
unprivileged theft/signing/retry exploit was confirmed in these inspected paths;
that is not assurance of absence across the whole system.
