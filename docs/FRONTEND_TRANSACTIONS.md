# Unsigned mint and claim preparation

`frontend_api.transactions` prepares two typed wallet actions using the existing
deployment-pinned [read service](FRONTEND_API.md). It constructs and simulates a
transaction draft, with no key, signature, broadcast, allowance or asset movement.
The public website remains a simulation. A separate local
[browser-wallet profile](BROWSER_WALLET.md) implements signing and receipt recovery
against disposable Anvil contracts. No production PoPL deployment is configured.

## Supported actions

| Action | Fixed target and call | Native value | Approvals |
| --- | --- | --- | --- |
| Dormant mint | Canonical Vault `mintDormant()` | Exactly 0.05 ETH | None |
| LP and royalty claims | Immutable NFT-owned router `claimBatch((uint256,address,bool)[])` | Zero | None |

Direct mint is an implemented unsigned backend capability and historical Anvil
path, **not an OpenSea primary mint integration**. The production qualification
gate rejects that unsupported OpenSea path; public website minting remains a
demonstration. Direct mint forwards the full 0.05 ETH to its recipient. The requested
OpenSea buyer total of 0.05 ETH/platform-fee split needs compatible code and review.
See [mint qualification](MINT_INTEGRATION_QUALIFICATION.md). Enabling transaction
configuration does not implement that path or enable signing.

The service accepts only the connected wallet's public address and the typed
selection. Callers cannot provide RPC URLs, chain IDs, destinations, recipients,
arbitrary calldata, overrides, nonce, gas settings or spending approvals.
The service does not authenticate control of that address: only the wallet's
later signature and the contracts can authorize a transaction.

Claims contain 1-32 operations, not 32 NFTs times every asset. Each operation
names an actual decimal-string uint256 token ID, an admitted asset and a strict
boolean selecting royalties or LP rewards. Duplicate operations are rejected;
the same NFT/asset in the two different ledgers is valid. Native address zero is
allowed for royalties and, under explicit accounting 2/3, native LP rewards. The same NFT
and native asset may select both distinct ledgers in one exact batch. Historical
profiles do not gain native-LP semantics from a manifest change. Every selected NFT must belong to the supplied
wallet, and every selected operation must have a positive funded balance.
Nothing silently drops failing entries or splits an oversized request.

Claims remain independent of global/mint pause, preparation, current LP valuation
and parking; frozen/importing/retired/cancelled canonical states block preparation.
The ledger/router simulation still enforces actual entitlement,
backing and payout callback behavior. Failed operations reject the entire draft.

## Optional HTTP endpoint

GET-only operation remains the default. To explicitly enable unsigned preparation
for a reviewed local deployment configuration:

```sh
python -m frontend_api.server --config /operator/path/frontend-read.json --transaction-config /operator/path/wallet-policy.json --port 8787
```

The read configuration pins the canonical chain, deployment anchor, eight core
contract runtimes/helper bindings and admitted reward assets. The separate policy
file is required to enable preparation; there is no default production fee policy:

```json
{
  "schema": 1,
  "chain_id": "<replace with actual integer chain ID>",
  "projection_sha256": "<exact reviewed Projection.identity, without 0x>",
  "fee_policy": {
    "estimate_includes_all_fees": true,
    "review_hash": "0x<nonzero 64-hex-digit hash of reviewed fee evidence>",
    "max_gas_price_wei": "<positive decimal operator ceiling>",
    "max_network_fee_wei": "<positive decimal operator ceiling>"
  }
}
```

These deliberately unusable placeholders must be replaced. `Projection.identity`
is SHA-256 over canonical JSON of the read configuration excluding `rpc_urls`
(sorted keys, compact separators), also exposed as `provenance.configuration_sha256`.
Compute it from the independently reviewed configuration; policy mismatches fail
at startup. RPC URL/credential rotation leaves this identity unchanged; changes
to deployment, assets or other read settings require re-review and a new binding.
The transaction policy has its own hash in the response.

The operator must confirm that `eth_estimateGas` multiplied by `eth_gasPrice`
accounts for **all** network fees. If separate L1/data charges are omitted, do
not attest true; extend the adapter first. A review hash records a review but
cannot establish its quality. No signer or wallet key belongs in these files.

The optional endpoint is:

```text
POST /v1/transactions/prepare
Content-Type: application/json
```

Mint request:

```json
{"action":"mint","wallet":"0x<current wallet address>"}
```

Mixed claim request:

```json
{
  "action":"claim",
  "wallet":"0x<current wallet address>",
  "claims":[
    {"token_id":"<actual decimal token ID>","asset":"0x<admitted ERC20>","royalty":false},
    {"token_id":"<actual decimal token ID>","asset":"0x0000000000000000000000000000000000000000","royalty":true}
  ]
}
```

Bracketed values are unusable examples, not configured accounts or addresses.
The endpoint requires one canonical Content-Length, at most 16 KiB, one expected
loopback Host and JSON content type. Duplicate JSON keys, transfer encoding,
malformed input and unexpected fields are rejected. There are no CORS grants,
request-body logs or upstream error disclosures. Typed input errors return 400,
unknown NFTs 404, unavailable verification/simulation 503. Work budgets and worker
supervision are implemented; public ingress, TLS, abuse limits and operating
qualification remain required before hosting.

## What a successful draft means

All state reads, simulation, gas estimation and wallet balance reads use **one
confirmed canonical block hash** with EIP-1898. The gas-price suggestion is a
preparation-time RPC quote, not a historical price. No `latest` fallback or state,
balance or allowance override. Mint preparation verifies the exact price, supply
cap, remaining supply, global pause, preparation mode and independent mint-pause
switch. Minting does not query unrelated reward currencies. Simulation exercises the actual mint,
VRF request and mint-recipient payment paths. Claims require the full reviewed
ledger inventory and core bindings, but isolate an unselected currency's failed
runtime/decimal check. Selected currency failures reject the whole draft;
terminal work limits are never swallowed. Actual simulation remains decisive.

For accounting3 claims, the preparer reads the global activation weight once per
distinct selected NFT at that same block. Only 0..3 is valid; weight0 plus a positive
LP/royalty claim balance is contradictory core data and rejects the draft. Missing
or malformed activation data also fails closed. This matches NFT read integrity;
the weight is not used to calculate the payout. Activated parked/outbound NFTs
and optional-currency deferrals retain their earned rights. Historical profiles
do not acquire this getter requirement. No optional currency read is added merely
to check activation. [Scoped review](../reports/reward-resilience-20261026/REVIEW.md).

Claims use an exact, narrowly encoded array and an exact sender/value simulation.
Results must contain the canonical uint256 array offset, count and bounded size.
Returned `view_raw` and `simulated_raw` are separate raw token-unit strings.
Royalty synchronization or legitimate recipient callbacks can affect subsequent
operations during the simulated batch. Different assets are never added into
one dollar figure, and simulation is not a promise of a future payout.

Simulation and estimation have a **12M gas work cap**. Estimates must be
21,000..12M; the suggested limit adds 20% headroom up to the cap. Gas price and
suggested-limit cost must fit the reviewed ceilings. Wallet balance must cover
native value plus that cost; future claim proceeds cannot pay upfront gas.
`network_gas` reports separate estimated/suggested costs, price and units, review
hash and required wallet refresh. No gas/nonce/fee fields are injected into the
transaction object. Smaller claim batches may be needed; these are estimates,
not guaranteed inclusion costs.

Direct calls share a 25-second work budget, finite RPC counts and snapshot expiry;
HTTP adds [bounded parallel admission](CONCURRENT_SERVICES.md), with one isolated
killable child per request and a 30-second supervisor limit. Failed or
expired results cannot become drafts, and terminal budget errors cannot be hidden
by per-currency isolation.

Before returning, the service rechecks block identity/timestamp, deployment
anchor, chain, current confirmation depth and freshness after the final network
response. Preparation additionally allows at most 120 seconds of snapshot age.
The draft expires at the earlier of 60 seconds after preparation or the source
snapshot's expiry. **This is a client-enforced expiry, not an on-chain deadline.**
Mint and claim calldata have no deadline argument.

The response includes:

- `transaction`: exact `from`, `to`, `data`, hex `value` and hex `chainId`.
- Separate claim-operation view/simulation amounts, asset labels and decimals.
- Snapshot hash/number/time, deployment anchor and configuration identity.
- `prepared_at`, `expires_at`, `wallet_revalidation_required: true`.
- Simulation success/cap/estimate, separate `network_gas`, and the transaction
  policy identity. No nonce, signature or broadcast.

No simulated mint ID is reserved or advertised. The actual confirmed
`DormantMinted`/NFT `Transfer` receipt determines the minted token. Mint inclusion
does not mean VRF has fulfilled and the ordered trait reveal has finalized.

## Browser integration requirements

The local [browser-wallet profile](BROWSER_WALLET.md) exercises these boundaries
with a fixture manifest and independent EIP-1193 submission. Actual extension
acceptance, production endpoint adaptation and reviewed public deployment/fee
policies remain open; its dynamic local manifest is not production authentication.

Before offering a real wallet confirmation, the frontend must:

1. Load independently reviewed deployment identities; do not trust a transaction
   destination merely because a backend returned it.
2. Verify the current wallet account and chain, the exact typed action/calldata,
   target, value and fresh draft expiry. Handle account/network changes by
   discarding pending drafts. Only mint and router claims need no approvals.
3. Recheck current ownership/admission/availability and simulate the exact request
   against fresh chain state; estimate current gas and present network cost
   separately. A confirmed snapshot does not include pending transactions.
4. Ask the user to authorize the exact wallet transaction. Handle rejection,
   replacement, failure and reorgs. Never automatically retry a payment.
5. Verify the canonical successful receipt from the expected sender/target before
   refreshing balances and complete lifetime claim history. LP and royalty ledger
   events are counted once; the router's batch event is not another reward.

The preparation endpoint itself supplies no wallet, reviewed deployment manifest
or production gas policy. It is an unhosted backend integration component.
Qualify its browser consumer and live services together before offering public
wallet transactions.

## Activation and additions stay separate

The existing eight read-service pins do not authenticate Entry, Registry, source
admission, Oracle and conversion routes. Activation requires those additional
reviewed identities, a complete original-source quote and a simulated marginal
LP deployment satisfying the captured contribution-loss budget. The current
ETH/fixed ZZZ candidate defaults to 2%, governed up to 10%, with its reviewed caller
ceiling and stricter execution minima still enforced. Historical 1% fixtures keep
their original policy/ABI; do not reuse their quotes for the current profile.

For ERC20 input, approve only the exact source amount to the immutable
Registry-created Entry. After approval confirmation, requote and simulate the
exact owner/Entry request before execution. Native ETH sends the exact amount
with zero source address. No NFT approval is needed. The separately configured
[complete Entry preparation service](ACTIVATION_PREPARATION.md) supplies this path;
use separate listeners for activation and mint/claim adapters.

Current activation/growth accepts native ETH or the one fixed ZZZ token only.
Actual feeds, routes/native venue, current website compatibility, authorities,
VRF, hosting, OpenSea integration and independent audit remain release gates.
Royalty currencies are separate and do not become contribution assets merely
because a royalty receipt is admitted.

## Verification

```sh
python -m unittest tests_python.test_frontend_transactions tests_python.test_frontend_transaction_http tests_python.test_wallet_preparation -v
```

Current activation-integrity regressions are in
`tests_python.test_claim_activation_integrity`; the latest
[combined affected report](../reports/reward-resilience-20261026/VERIFICATION.md)
records the exact selected modules and source pins without adding overlapping runs.

Tests cover exact intent/ABI, uint256 precision, mixed/native claims, 32-operation
limits, owners, caps, pause-independent claims, unavailable balances, deployment
pins, stale/reorged snapshots, malformed simulations, and actual loopback HTTP
input/error boundaries. Frozen ABI vectors were independently checked against
the actual router using Solidity `abi.encodeCall`. Offline RPC fixtures are not
live service, production wallet or authority qualification.

The [source-scoped evidence](../reports/wallet-preparation/VERIFICATION.md) distinguishes
reused compiler evidence from current Python tests. See the
[operator procedure](OPERATOR_MANUAL.md#unsigned-mint-and-claim-service) to enable,
disable and recover this service without changing contract permissions.
