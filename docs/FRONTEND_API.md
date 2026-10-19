## Processed earnings extension - 2026-10-19

Optional `earnings_history` adds read-only `GET /v1/earnings` and
`GET /v1/nfts/<decimal-token-id>/earnings`. They reconstruct separate processed
LP/collective/royalty earnings for all time and the last 24 hours. The user's USD
policy is **current confirmed prices**, not historical dollars. Claims and
conversion credits are separate. Review all seven emitters from creation, full
predecessor coverage and price pins before enabling. See [configuration and
recovery](EARNINGS_HISTORY.md) and [evidence](../reports/earnings-history/VERIFICATION.md).
Existing position responses do not silently fetch this additional history.
Live deployment and frontend integration remain open.

## Current royalty reporting extension - 2026-10-19

The optional [royalty reporting profile](ROYALTY_REPORTING.md) adds verified
per-currency eligibility, explicit unavailable balance fields and pinned converter
enable status to the single-NFT read. ETH balances include unclaimed conversion
credits; source balances are not promised ETH payments. Core deployment/lifecycle,
complete-history and final snapshot checks stay strict. Legacy all-or-nothing
currency behavior below applies when this profile is absent; wallet inventory
and financial-action validation retain their existing strict paths.

Complete history now also returns `royalty_conversions`, separately from actual
lifetime `previously_claimed`. See [field semantics and operator recovery](ROYALTY_REPORTING.md)
and [scoped evidence](../reports/royalty-reporting/VERIFICATION.md). This is backend
implementation; processed earnings/current-price USD now have their own
[optional profile](EARNINGS_HISTORY.md). Neither is a deployed service or live UI.

# Confirmed frontend read API

The `frontend_api` package is a working read-only Python 3.11+ service for
**individual canonical NFTs and confirmed wallet inventories**. It reads deployed contracts, rather than using
website demo balances. It has no private keys, signer, transaction broadcast,
administrator write endpoint, invented balances or external dependencies. An
explicit opt-in [unsigned mint/claim preparation endpoint](FRONTEND_TRANSACTIONS.md)
can construct and simulate typed transaction drafts; default operation stays GET-only.
It has not been deployed or operated against a production PoPL deployment.

## Implemented endpoint

```text
GET /v1/protocol
GET /v1/nfts/{canonical-decimal-token-id}
GET /v1/wallets/{nonzero-Ethereum-address}/nfts
```

Token IDs are the actual uint256 identities, not mint ordinals or website
example numbers. JSON returns large token-unit integers as decimal **strings**;
never convert them to JavaScript `Number` for accounting.

Configuration and read responses use **schema 2**. The [lifecycle boundary](FRONTEND_LIFECYCLE.md)
requires two additional canonical helper pins. Locked deployments refuse NFT
and wallet projections; `/v1/protocol` remains available for verified lifecycle
and source-committed successor information without reading reward balances.

The response contains:

- Current owner, actual mint ordinal, reveal status and revealed rarity/palette/pattern.
- Strict canonical lifecycle, pause/preparation state, original identity and
  predecessor/successor information at the same confirmed hash.
- Canonical vault state, shared-bucket identity, nonredeemable shares and persistent
  activation/royalty eligibility.
- Explicit `parked` custody (appended on-chain status 6), authenticated local
  Vault location and zero physical LP ID. Claims and eligibility remain available;
  current LP valuation is unavailable, and the API does not invent continued
  revenue from a closed position.
- Current marked LP value from `ZZZNFT.currentLPValue`, in USD with 18 decimals.
  If the contract reports unavailable, `raw` is `null`; it is never displayed as
  zero. Evolution can decrease with current value, independently of activation.
- Actual `ZZZRewards.claimable` amounts for every admitted LP reward asset.
  This is the combined individual and collective balance already allocated by
  the contracts. Pending creator-receiver funds are **not** preview-synchronized.
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
503. These position endpoints do not reconstruct earned history. Use the
separate [earnings endpoints](EARNINGS_HISTORY.md) for processed all-time/24h
LP/collective/royalty earnings and optional current-price USD values. Claimable and lifetime
claimed amounts are not lifetime gross revenue. No assumed historical token
price or current-balance subtraction is substituted.

For imported successors, the optional [predecessor history](FRONTEND_LINEAGE.md)
configuration verifies and combines the complete same-chain LP/royalty claim
lineage. Without it, `previously_claimed` remains explicitly unavailable.
Current-deployment claims must never be presented as the NFT's lifetime total.

These endpoints are an unhosted integration foundation. The existing `indexer/`
remains unchanged; the new read-only history consumer validates its exact
confirmed snapshot and replays both ledgers. Actual price/ingestion qualification, live website integration and
operating rehearsals remain release work. Native contract batched claims are a separate `ZZZClaimRouter`
capability; this read service neither invokes it nor guarantees execution at a
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
    "vault_canonical": {"address": "0x<40 hex digits>", "code_hash": "0x<64 hex digits>"}
  },
  "assets": [
    {"address": "0x0000000000000000000000000000000000000000", "decimals": 18, "symbol": "ETH", "code_hash": null},
    {"address": "0x<ERC20 address>", "decimals": 18, "symbol": "ZZZ", "code_hash": "0x<64 hex digits>"}
  ]
}
```

Choose `deployment_block` at or after all eight pinned contracts and immutable helpers
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
valid only in the royalty list. LP rewards remain admitted ERC20s. Symbols are
reviewed display labels, not prices. An on-chain asset addition requires updating
and reviewing this configuration before the endpoint becomes available again.
ERC20 `decimals()` must match its configured descriptor at the same pinned block.

## Consistency and failure behavior

For each request, the service selects `head - confirmations + 1`, checks the
deployment anchor and header age, and uses EIP-1898
`{"blockHash": "...", "requireCanonical": true}` for every `eth_call` and
`eth_getCode`. Providers that do not support hash-pinned calls fail closed; no
fallback to `latest` or a number-only call is used.

Every request verifies eight runtime pins; sealed module bindings; their common
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

The server binds **127.0.0.1 only** and processes requests serially to bound
upstream concurrency. It validates loopback Host including the selected port
and uses five-second client socket/read-RPC timeouts. Do not expose Python's
standard-library HTTP server directly to the internet. A separately reviewed
HTTPS reverse proxy must set `Host: 127.0.0.1:8787`, strip incoming proxy headers,
bound request/header/connection sizes and time, rate-limit expensive requests,
cap queue/concurrency, and enforce same-origin website access. No proxy or public
service is installed by this change. A per-request end-to-end operating budget,
monitoring, archive-provider coverage and realistic load/failover rehearsals
remain production gates; serial reads deliberately prioritize consistency over
throughput. Keep credential-bearing configuration files out of source control.

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
cleanup waits of up to one second each; an unreaped worker blocks further work.
Direct library users share cooperative limits but do not get the process supervisor
unless they use WorkerClient. DNS/body stalls require that supervisor.

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
`new_minting_stopped`, which combines mint-only pause with the existing global /
canonical / preparation lifecycle restriction. `new_minting_stopped_by_lifecycle`
keeps its original narrower meaning. These fields do not prove provider funding,
fulfillment, remaining supply or successful execution. LP contribution availability
is not turned off merely because minting is paused.

All reads use the same confirmed hash and final canonicality check; missing or
malformed getters fail rather than assuming minting is open. Deployment pins must
match this NFT implementation. Existing deployments without `mintPaused()` need
a compatible service version. See [controls evidence](../reports/operator-controls/VERIFICATION.md).
