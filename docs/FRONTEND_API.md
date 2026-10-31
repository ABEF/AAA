# Confirmed frontend read API

Confirmed financial history rejects contradictory transaction-index/hash grouping
at ingestion and replay. Valid filtered-log gaps and optional historical indices
remain supported; consistency does not prove provider/database completeness.
Observation also rechecks final confirmation depth and signed legacy gas-price
agreement. Contradictory evidence is an error/unavailable amount, never guessed 0.
See [current review](../reports/whole-project-execution-20261029/BACKEND.md).

The `frontend_api` Python service reads confirmed contract state and optional
complete indexed history. It has no private keys, signer, broadcast method or
administrator write endpoint. Optional typed preparation returns simulated,
unsigned drafts only; public signing remains disabled. Production hosting,
current-profile website integration and actual dependencies are not qualified.

Fresh source uses accounting6, maintenance3, confirmation3 and optional portfolio2.
Ordinary samples require the physical pool and independent reference on the same
85%-of-centre-to-boundary threshold side in ZZZ-in-ETH price, using actual rounded
main bounds. This threshold can be reached while the main remains active. The
600-second sampled window may accumulate during the hard twelve-hour cooldown;
execution needs both, then one persisted 60–300-second keeper delay. Source checks
are 240 seconds; the configured maximum confirmed gap is 300 seconds. A gap-0 helper
is unconfigured and cannot authorize ordinary sampled execution. Earlier
maintenance2/confirmation2 deployments retain their outside-only policy and selected 900/300 settings; other historical profiles stay explicit.

A separate paused governance emergency capability2 may explicitly bypass chosen
financial/timing checks; exact custody/accounting remain, but near-total economic
loss is possible. It is not an automatic keeper fallback or API signing feature.
Live independent sources/routes remain unqualified. [Execution policy](LP_EXECUTION_POLICY.md),
[optional portfolio](OPTIONAL_PORTFOLIO_IMPLEMENTATION.md), [emergency procedure](EMERGENCY_REBALANCE.md).

## Current deployment profile

Fresh configuration uses explicit `accounting_version:6` and `fee_intake_version:1`
with read schema2. It verifies Vault6, direct governance2, custody4 and the
explicit `ZZZ_CANONICAL_SAME_CHAIN_ADAPTABLE_POLICY_V6` admission domain. Position still has
eight words; dormant/parked/exited states remain 3/4/5. The main physical LP ID is
never replaced by an aggregate or virtual ID.

Profile6 requires these additional `{address,code_hash}` pins, beyond the existing
base contracts and `principal_exit`:

| Boundary | Explicit contract roles |
| --- | --- |
| Principal and strategy | `pools`, `liquidity`, `strategy`, `budget` |
| Protocol and strategy policy | `protocol_policy`, `portfolio_policy`, `rebalance_confirmation` |
| Typed LP execution | `balancing_router`, `lp_balance_math`, `lp_position_executor` |
| Reviewed v4 dependencies | `pool_manager`, `state_view`, `position_manager`, `permit2` |

The service verifies runtime, sealed module, parent/child and dependency bindings.
Capabilities are accounting6/maintenance3/confirmation3/compound4/custody4,
LP routing2/portfolio2/execution quality1 and emergency2. Math is noncustodial;
the fixed PositionExecutor accepts only Manager's typed LP operations. No new
wallet, signing authority, generic executor or custody recipient is introduced.

Active positions authenticate the actual main and optional residual owners,
full PoolKeys, ticks and positive liquidity at the same canonical block.
`Manager.amounts(actualId)` remains physical; `portfolioAmounts(main)` must equal
the exact two-leg sum. `position.local_custody.portfolio` exposes both IDs/bounds,
raw physical principal, desired mode and pending geometry. NFT LP USD value also
includes attributed idle/compound through the existing on-chain share valuation.
Collection/wallet chunks reuse a verified bucket only within that request; there
is no cross-user/latest-state cache. A missing or contradictory leg fails closed.
Desired single mode does not erase a residual awaiting atomic merging.

Accounting6 uses an explicit physical-only observation for this authentication.
It skips maintenance-price diagnostics, not owners, runtime bindings, PoolKeys,
main range geometry consistency, positive liquidity or aggregate raw amounts.
A reference-price outage therefore leaves confirmed ownership and funded raw
claim balances available; LP/USD valuation can remain unavailable. Contradictory
physical evidence still fails closed. Physical-only results carry no `allowed`,
`status` or maintenance readiness assertion. The default keeper observation
retains price/eligibility checks. [Regression evidence](../reports/day-audit-20261031/VERIFICATION.md).

Optional residual mode is disabled by default. Its approved default is half of
the corresponding main side (`residualSideBps=5000`), with an actual tick-spacing
gap; governance may review another fraction from 1 to 10000. For a main 50–150 around 100,
the outer targets are 75 or 125, not a forced 40% capital allocation. Ordinary
replacement proves the configured main floor(default60%, hardminimum60%) and
complementary residual ceiling(default40%) at captured USD marks. Subsequent market changes may alter
those percentages or make a residual mixed; the API must not call all capital
active or continuously 60% active.

The optional schema1 activation configuration explicitly declares range1,
maintenance3, LP routing2, execution quality1, confirmation3, reviewed Entry2 and `portfolio_version:2`.
It pins ProtocolPolicy1/PortfolioPolicy2/Confirmation/BalanceMath/PositionExecutor
as well as existing helpers. ProtocolPolicy version1 is explicit on the read
configuration; the activation subsection inherits it rather than accepting a duplicate key. Shared read/preparation pins and venue dependency hashes must match.
The unsigned context distinguishes physical threshold, independent agreement,
cooldown, sampled maturity and actual readiness; it reports no promised keeper
time. Its execution portfolio fingerprint includes current liquidity, while the
confirmation identity excludes mutable liquidity so another contribution does
not reset the window. Exact simulated deployment follows
Vault→Manager→PositionExecutor→PosM; later Policy bookkeeping reads cannot count
as marginal LP. Entrant funds increase/create only the main, not an incumbent
inventory-repair residual. [Preparation](ACTIVATION_PREPARATION.md).

Accounting1-5 readers remain explicit historical profiles. Omitting the version
selects legacy1, never6. Their codecs, addresses, runtimes, timing and journals
are not rewritten. API6 predecessor history requires explicit accounting6 and canonicalV6
throughout; the retained record shape does not authorize relabelling old V5
accounting4/5 history. Historical accounting4 remains a separately pinned custody3 profile.

Production inventory schema8 is separate from read schema2 and activation schema1;
it authenticates the complete fresh helper graph. Historical schema7/6 stay tied
to their recorded profiles. Actual provider/route/VRF/gas/service qualification is
still open. The served poplint accounting3 artifact remains unconfigured;
popldemo remains the separate simulation. Source changes do not deploy either
site, change Anvil, or enable public signing. Browser signing remains Anvil-only.

Fee-intake1 history still verifies actual funded-credit/allocation pairing and
final dust. Native ETH is address zero, without a wrapper or presumed USD peg.
Validated dormant NFTs cannot report positive available rewards. Currency outages
may leave the affected metric unavailable; contradictory core data is an error.
See [earnings semantics](EARNINGS_HISTORY.md) and [royalty reporting](ROYALTY_REPORTING.md).

After governance starts collective exit, `lifecycle.lp_exit_started` is permanent.
Mint/contribution preparation stops; NFT transfers and earned LP/royalty claims
remain available. Exited NFTs report verified zero LP and `evolution: lp_exited`,
while retaining their royalty weight. NFT/collection rows include a separate
`principal_return`: phase, current-owner beneficiary, allocated/paid flags and
ETH/ZZZ `allocated_raw`, `remaining_raw`, `claimable_raw`. Unallocated or not-yet
claimable values are null. Paid allocations remain historical amounts with zero
remaining principal. These amounts never enter rewards, earnings or previously
claimed reward totals. No principal-payout transaction endpoint is implemented.

## Implemented endpoint

| GET path | Purpose / optional configuration |
| --- | --- |
| `/v1/protocol` | Verified lifecycle, controls and source-committed successor information |
| `/v1/mint-readiness` | Confirmed reveal inventory; not randomness-provider or mint-execution approval |
| `/v1/nfts/{token-id}` | Canonical owner, traits, LP value, current claimable balances and available history |
| `/v1/wallets/{address}/nfts` | Complete confirmed ownership inventory; requires creation-to-cutoff history |
| `/v1/wallets/{address}/summary/{block}/{offset}` | Up to 16 current holdings' LP/ETH values; complete every matching chunk before totaling |
| `/v1/collection/{block}/{offset}` | Up to 16 canonical positions and chunk LP totals; see [collection reads](COLLECTION_READS.md) |
| `/v1/earnings` | Processed collection LP/royalty history; requires `earnings_history` |
| `/v1/nfts/{token-id}/earnings` | That NFT's processed lifetime/24h earnings, including previous owners |
| `/v1/wallets/{address}/earnings/{block}/{offset}` | Up to 16 current holdings' lifetime earnings; requires `earnings_history` |

Base protocol/NFT/inventory/readiness responses use schema 2. Collection,
summary and earnings chunk responses have their own schema 1 under that same
schema 2 deployment configuration. Do not infer a contract profile from a response
schema number. Optional [unsigned preparation](FRONTEND_TRANSACTIONS.md) is enabled
separately; the ordinary read listener remains GET-only.

Token IDs are the actual uint256 identities, not mint ordinals or website
example numbers. JSON returns large token-unit integers as decimal **strings**;
never convert them to JavaScript `Number` for accounting.

The [lifecycle boundary](FRONTEND_LIFECYCLE.md)
requires two additional canonical helper pins. Locked deployments refuse NFT
and wallet projections; `/v1/protocol` remains available for verified lifecycle
and source-committed successor information without reading reward balances.

The response contains:

- Current owner, actual mint ordinal, reveal status and revealed rarity/palette/pattern.
- Strict canonical lifecycle, pause/preparation state, original identity and
  predecessor/successor information at the same confirmed hash.
- Canonical vault state, shared-bucket identity, nonredeemable shares and persistent
  activation/royalty eligibility.
- Explicit `parked` custody (current on-chain status 4), the authenticated local
  Vault and zero physical LP ID. Claims and eligibility remain available;
  current LP valuation is unavailable, and the API does not invent continued
  revenue from a closed position.
- Current marked LP value from `ZZZNFT.currentLPValue`, in USD with 18 decimals.
  If the contract reports unavailable, `raw` is `null`; it is never displayed as
  zero. Evolution can decrease with current value, independently of activation.
- Actual `ZZZRewards.claimable` amounts for every admitted LP reward asset.
  This is the combined individual and collective balance already allocated by
  the contracts. The hookless release has no creator-payment inbox or remote fee intake.
- Actual `ZZZRoyaltyRewards.claimable` amounts for every admitted royalty asset,
  including address-zero native ETH. This contract view includes pending
  admitted receipts at current membership weights. LP and royalties are separate
  arrays; amounts in different currencies are not summed.
- Verified canonical NFT/helper contract addresses, including `claim_router`.
  The API never requests approval, constructs a signature or submits a claim.
- Block number/hash/timestamp, observed head, confirmation depth, deployment
  anchor and configuration identity. `protocol_finalized` is **false**: configured
  confirmation depth is not a proof of L1 settlement or protocol finality.

With optional [confirmed indexer history](FRONTEND_HISTORY.md), wallet inventory
and cumulative `previously_claimed` LP-plus-royalty amounts are now implemented.
They require exact creation-to-target coverage and raw-log replay; current
ownership additionally agrees with on-chain counts/owners. Without that
configuration, NFT history is explicitly unavailable and wallet requests fail
503. The inventory endpoint isolates per-currency runtime/decimal read failures:
an optional royalty currency outage does not hide verified ownership. It returns
no currency balances or valuations; admitted address inventories, core module
bindings, complete history, current owners and canonical confirmation checks
remain strict. Financial endpoints retain their own unavailable-currency rules.
These position endpoints do not reconstruct earned history. Use the
separate [earnings endpoints](EARNINGS_HISTORY.md) for processed all-time/24h
LP/collective/royalty earnings and optional current-price USD values. Claimable and lifetime
claimed amounts are not lifetime gross revenue. No assumed historical token
price or current-balance subtraction is substituted.

For imported successors, the optional [predecessor history](FRONTEND_LINEAGE.md)
configuration verifies and combines the complete same-chain LP/royalty claim
lineage. Without it, `previously_claimed` remains explicitly unavailable.
Current-deployment claims must never be presented as the NFT's lifetime total.

These endpoints are an unhosted integration foundation. The read-only history
consumer validates the configured indexer's exact confirmed snapshot and replays
both ledgers. Actual price/ingestion qualification, live website integration and
operating rehearsals remain release work. Native contract batched claims are a
separate `ZZZClaimRouter` capability; this read service neither invokes it nor guarantees execution at a
later block. The wallet must recheck owner/network and simulate immediately
before signing. A quoted confirmed balance can change before execution.

## Deployment configuration

The configuration is an operator-reviewed JSON file, outside the public web
document root. No PoPL addresses have been chosen/deployed by this implementation.
The required base shape is below; bracketed values are **unusable placeholders**, not
an approved deployment configuration. The optional strict `history` object is
specified in [history configuration](FRONTEND_HISTORY.md#configuration-and-genuine-coverage):

```json
{
  "schema": 2,
  "accounting_version": 4,
  "fee_intake_version": 1,
  "chain_id": 46630,
  "rpc_urls": ["https://<reviewed-provider>"],
  "deployment_block": 123,
  "deployment_block_hash": "0x<64 hex digits>",
  "confirmations": 12,
  "max_block_age_seconds": 120,
  "contracts": {
    "access": {"address": "0x<40 hex digits>", "code_hash": "0x<64 hex digits>"},
    "nft": {"address": "0x<40 hex digits>", "code_hash": "0x<64 hex digits>"},
    "vault": {"address": "0x<40 hex digits>", "code_hash": "0x<64 hex digits>"},
    "rewards": {"address": "0x<40 hex digits>", "code_hash": "0x<64 hex digits>"},
    "royalties": {"address": "0x<40 hex digits>", "code_hash": "0x<64 hex digits>"},
    "claim_router": {"address": "0x<40 hex digits>", "code_hash": "0x<64 hex digits>"},
    "handoff": {"address": "0x<40 hex digits>", "code_hash": "0x<64 hex digits>"},
    "vault_canonical": {"address": "0x<40 hex digits>", "code_hash": "0x<64 hex digits>"},
    "principal_exit": {"address": "0x<40 hex digits>", "code_hash": "0x<64 hex digits>"}
  },
  "assets": [
    {"address": "0x0000000000000000000000000000000000000000", "decimals": 18, "symbol": "ETH", "code_hash": null},
    {"address": "0x<ERC20 address>", "decimals": 18, "symbol": "ZZZ", "code_hash": "0x<64 hex digits>"}
  ]
}
```

Choose `deployment_block` at or after all nine pinned contracts and immutable helpers
exist and the access controller is sealed. Pin its independently checked block
hash. Chain 46630 is Robinhood Testnet; chain 4663 is Robinhood mainnet. Network
choice, twelve confirmations and 120 seconds above are examples requiring a
reviewed chain-specific finality/outage policy, not approved production settings.

Runtime `code_hash` is Ethereum **Keccak-256 of deployed runtime bytecode**,
including constructor-resolved immutable values, not SHA-256 or initcode hash.
Source/build verification and deployment receipts must supply the expected
identity independently of the RPC used to serve the site. ERC20 proxy runtime
hashes alone do not pin their implementation, underlying backing or upgrade
authority: their governance/implementation policy still needs separate review.

The asset descriptors must match the **exact union** of both admitted on-chain
asset lists; no silently omitted assets or unreviewed decimal/symbol guesses are
allowed. Native ETH has address zero, 18 decimals and `code_hash: null`; it is
valid in both current native LP and royalty ledgers. Historical accounting1
profiles retain their original ERC20-only LP boundary. Symbols are
reviewed display labels, not prices. An on-chain asset addition requires updating
and reviewing this configuration before the endpoint becomes available again.
ERC20 `decimals()` must match its configured descriptor at the same pinned block.

## Consistency and failure behavior

For each request, the service selects `head - confirmations + 1`, checks the
deployment anchor and header age, and uses EIP-1898
`{"blockHash": "...", "requireCanonical": true}` for every `eth_call` and
`eth_getCode`. Providers that do not support hash-pinned calls fail closed; no
fallback to `latest` or a number-only call is used.

Historical accounting4 verifies its nine base runtime pins and accounting5 its
explicit old portfolio graph. Accounting6 additionally authenticates ProtocolPolicy1
and Portfolio2 with the complete execution/dependency graph above.
Every request checks sealed module bindings and their common
controller; the Vault's home chain; NFT/royalty/helper ownership; and canonical
lifecycle/origin. NFT and wallet requests additionally verify the full admitted
asset inventory and asset code/decimals. The status endpoint omits those asset
reads so moved backing or token outages do not hide the deployment's lifecycle.
It checks the selected block's full identity/timestamp and deployment anchor,
current confirmation depth and final freshness again before releasing a
successful result. Provider failover onto a competing fork, an anchor mismatch,
stale/future headers, ABI failures, wrong bindings, unknown asset admission or
changed runtime code produce an unavailable response. There is **no cache** to
invalidate or serve across reorgs. A reorg after the response remains possible;
the response hash/depth lets downstream consumers identify its exact snapshot.

The RPC URL, chain, target contracts and assets are fixed by operator
configuration. The user cannot supply an arbitrary RPC, contract, block, call
data or method. The shared RPC client independently checks chain ID for every
upstream request and refuses signing/broadcast methods.

HTTP status behavior:

CLI services additionally enforce [client admission](API_INGRESS.md): 429
`client_busy` / `client_rate_limited`, 503 `admission_capacity_unavailable`, and
400/403 for invalid explicit proxy identity/origin. Respect `Retry-After` with
bounded read retries; none of these responses is a zero balance or a transaction
submission. Public proxy errors may have a non-JSON body; check status first.

| Status | Meaning |
| --- | --- |
| 200 | Verified protocol status, NFT snapshot, or history-backed wallet inventory |
| 400 | Invalid Host, request body or out-of-range token ID |
| 404 | Unknown endpoint/noncanonical path, or NFT without a mint ordinal |
| 405 | Method other than GET when optional unsigned preparation is disabled |
| 503 | Locked deployment or unavailable confirmed projection; do not substitute demo/zero values |

Errors do not disclose RPC URLs, upstream error messages or credentials.
Responses use `Cache-Control: no-store` and no cross-origin grants. The server
does not log request paths/query strings.

With `--transaction-config /operator/path/wallet-policy.json`, only `POST /v1/transactions/prepare` is additionally
enabled. It uses strict 16 KiB JSON input and returns unsigned, expiring simulated
mint/claim drafts with separate reviewed gas estimates. See its [separate request and wallet rules](FRONTEND_TRANSACTIONS.md);
this does not turn on any signing or broadcast capability.

## Local operation and verification

From this repository root, using a reviewed deployment configuration:

```sh
python -m frontend_api.server --config /path/to/frontend-read.json --port 8787
python -m unittest tests_python.test_frontend_api -v
```

The server binds **127.0.0.1 only**. It now defaults to four independent spawned
request workers and eight bounded HTTP connections, with no expensive-work waiting
queue. Set `--workers` (1-8) and `--max-connections` (1-32) explicitly when sizing
the service. Full capacity returns HTTP 503 `service_busy` / `Retry-After: 1`.
Each request owns its Projection, RPC client, database reader and budget; financial
results are not cached across users. See [concurrent operation](CONCURRENT_SERVICES.md)
for exact ingress/header/deadline limits, logs, sizing and stop/restart procedures.

Do not expose Python's standard-library server directly to the internet. A reviewed
HTTPS proxy must set `Host: 127.0.0.1:8787`, strip incoming proxy headers, bound
request/header/connection/response sizes and time, rate-limit expensive requests,
cap queue/concurrency, and enforce same-origin access. No proxy or public service
is installed by this change. Actual provider capacity, monitoring, archive coverage
and realistic Linux load/failover rehearsals remain production gates. Keep
credential-bearing configuration files out of source control.

The tests exercise actual static ABI encodings and mocked contract-returned
balances, native royalty receipts, decimal precision, ownership changes, current
value downgrades, unavailability without loss of claims, strict deployment and
asset checks, reorg rejection, unsupported EIP-1898, malformed ABI/input, and real
loopback HTTP error/no-cache behavior. They are offline integration evidence,
not a deployment, live-chain service rehearsal or independent audit.

## Request limits and mint-readiness observation

The read and activation command-line HTTP servers use supervised spawned read-only
request workers. Shared projection/preparation work has a 25-second monotonic
budget, 1,024 logical RPC calls and 2,048 physical RPC POSTs (including retry and
chain-check work). Snapshot/quote expiry shortens the deadline; nested history,
lineage and trace work cannot reset it. SQLite queries use a progress callback.
The parent stops a request at 30 seconds including startup, with terminate/kill
cleanup waits of up to one second each. Failed process/directory cleanup quarantines
that supervisor slot until operator recovery; other healthy slots continue.
Direct library users share cooperative limits but do not get the process supervisor
unless they use WorkerClient or WorkerPool. RPC stalls require that supervisor.

Timeouts/work exhaustion return unavailable, never partial history or an expired
transaction. Logs contain only sanitized outcome/elapsed fields. Public ingress,
queue/rate/connection limits and actual Linux/RPC operating qualification remain
required; these local controls are not hosted-service approval.

`GET /v1/mint-readiness` returns a confirmed consistent mint/reveal inventory and
oldest unfinished request/epoch (awaiting randomness or ordered finalization).
The reveal condition alone does not approve handoff. Provider funding/liveness,
pending duration and other handoff requirements remain explicitly unverified.
It performs no signing or finalization and deploys no watcher. See [the operator
procedure](OPERATOR_MANUAL.md#mint-and-metadata) and [evidence](../reports/api-work-limits/VERIFICATION.md).

## Independent mint control

The confirmed `/v1/protocol` response includes `minting.paused` and
`minting.available_by_controls`. `/v1/mint-readiness` includes `mint_paused` and
`new_minting_stopped`, which combines exhausted 1,000-NFT supply, mint-only pause
and the existing global/canonical/preparation lifecycle restriction. Derived
`remaining_mint_supply` and `new_minting_stopped_by_supply` identify the cap
separately, with no extra RPC. Pending randomness/finalization stays observable
after sellout; sold out is not a VRF outage. Schema 2 and historical/current
profile identities remain unchanged. `new_minting_stopped_by_lifecycle`
keeps its original narrower meaning. These fields do not prove provider funding,
fulfillment, future mint availability or successful execution. LP contribution availability
is not turned off merely because minting is paused.

All reads use the same confirmed hash and final canonicality check; missing or
malformed getters fail rather than assuming minting is open. Deployment pins must
match this NFT implementation. Existing deployments without `mintPaused()` need
a compatible service version. See [controls evidence](../reports/operator-controls/VERIFICATION.md).

## Wallet summary chunks

`GET /v1/wallets/{address}/summary/{block-number}/{offset}` returns schema 1
summary chunks under the same schema 2 reviewed deployment. Each chunk covers
at most 16 holdings. Use the wallet inventory snapshot, offsets 0/16/32, and
require the same inventory digest, ordered IDs, owner, count and canonical block.
Only display totals once every chunk is verified; never present partial sums.
LP uses currentLPValue; funded ETH combines LP and royalties. Missing values
remain null. Historical earnings and unconverted source currencies are excluded.
See [aggregation and recovery procedure](LOCAL_API_REHEARSAL.md#full-wallet-totals).

## Accounting6 policy observation

Fresh reads explicitly require protocol_policy_version1 and the reviewed bound
helper/runtime. Dynamic sale/VRF mint provenance is `mint_policy`, separate from
`claim_operations` (empty for mint). Entry minima/idle and cosmetic tier thresholds
are read at the same confirmed block; missing policy never becomes guessed
defaults. Stage1 means actual activation, not a persistent100USD value floor.
Inventory is schema8; public signing remains disabled. [Exact profile](POSITION_V6.md).
