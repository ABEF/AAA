# Confirmed frontend read API

The `frontend_api` package is a working read-only Python 3.11+ service for
**individual canonical NFTs and confirmed wallet inventories**. It reads deployed contracts, rather than using
website demo balances. It has no private keys, signer, transaction broadcast,
administrator write endpoint, simulation balances or external dependencies.
It has not been deployed or operated against a production PoPL deployment.

## Implemented endpoint

```text
GET /v1/nfts/{canonical-decimal-token-id}
GET /v1/wallets/{nonzero-Ethereum-address}/nfts
```

Token IDs are the actual uint256 identities, not mint ordinals or website
example numbers. JSON returns large token-unit integers as decimal **strings**;
never convert them to JavaScript `Number` for accounting.

The response contains:

- Current owner, actual mint ordinal, reveal status and revealed rarity/palette/pattern.
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
  The API does not request approval, construct a signature or submit a claim.
- Block number/hash/timestamp, observed head, confirmation depth, deployment
  anchor and configuration identity. `protocol_finalized` is **false**: configured
  confirmation depth is not a proof of L1 settlement or protocol finality.

With optional [confirmed indexer history](FRONTEND_HISTORY.md), wallet inventory
and cumulative `previously_claimed` LP-plus-royalty amounts are now implemented.
They require exact creation-to-target coverage and raw-log replay; current
ownership additionally agrees with on-chain counts/owners. Without that
configuration, NFT history is explicitly unavailable and wallet requests fail
503. All-time/24h **gross generated fees**, reward USD conversion and unsettled
individual/collective breakdown remain unavailable. Claimable and lifetime
claimed amounts are not lifetime gross revenue. No assumed historical token
price or current-balance subtraction is substituted.

These endpoints are an unhosted integration foundation. The existing `indexer/`
remains unchanged; the new read-only history consumer validates its exact
confirmed snapshot and replays both ledgers. Complete gross fee attribution,
reviewed USD prices, transaction preparation, live website integration and
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
  "schema": 1,
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
    "claim_router": {"address": "0x<40 hex digits>", "code_hash": "0x<64 hex digits>"}
  },
  "assets": [
    {"address": "0x0000000000000000000000000000000000000000", "decimals": 18, "symbol": "ETH", "code_hash": null},
    {"address": "0x<ERC20 address>", "decimals": 18, "symbol": "ZZZ", "code_hash": "0x<64 hex digits>"}
  ]
}
```

Choose `deployment_block` at or after all six contracts and immutable helpers
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

Every request verifies six runtime pins; sealed canonical NFT/Vault/Rewards
bindings; their common controller; the Vault's home chain; NFT/royalty/helper
immutable backlinks; the full admitted asset inventory; and asset code/decimals.
It checks the selected block and deployment anchor again before releasing a
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
| 200 | Complete verified NFT snapshot, or history-backed wallet inventory |
| 400 | Invalid Host, request body or out-of-range token ID |
| 404 | Unknown endpoint/noncanonical path, or NFT without a mint ordinal |
| 405 | Method other than GET |
| 503 | Confirmed projection unavailable; do not substitute demo/zero values |

Errors do not disclose RPC URLs, upstream error messages or credentials.
Responses use `Cache-Control: no-store` and no cross-origin grants. The server
does not log request paths/query strings.

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
