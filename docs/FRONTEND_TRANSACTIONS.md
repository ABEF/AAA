# Unsigned mint and claim preparation

**Mint-profile boundary:** the backend implements explicit opt-in
`mint_integration_version:2` for accounting7/V10 reads and owned reward claims.
On accounting7, omitted/default1 retains the historical direct-mint/V9 profile; source9 website
configurations are unchanged. [SeaDrop mint2/schema17/V10](OPENSEA_MINT.md) still
requires reviewed matching deployment/configuration and operating acceptance.
No existing service, checkpoint, journal, served site or signer is upgraded or
relabeled by these source changes.


`frontend_api.transactions` prepares owned reward claims using the
deployment-pinned [read service](FRONTEND_API.md). Historical/default mint
integration1 also supports direct mint drafts. Explicit mint integration2 reads
V10 and prepares claims, but rejects a mint action with "Use OpenSea" before any
RPC, simulation or direct-Vault draft. It has no key, signature, broadcast,
allowance or asset movement.
The public website remains a simulation. A separate local
[browser-wallet profile](BROWSER_WALLET.md) implements signing and receipt recovery
against disposable Anvil contracts. No production PoPL deployment is configured.

## Reviewed gas policy2 (operator configuration)

Contract sealing does not freeze backend software/configuration. Historical
transaction policy1 keeps its exact12M ceiling and schema1 response. Optional
policy2 adds `fee_policy.max_gas_limit` as a canonical decimal string, with
engineering bounds21000–64000000. This is a service resource bound, not a claim
about Robinhood's block/transaction/RPC limits. The checked-in [example](../config/frontend-transactions.v2.example.json)
is deliberately unqualified and retains12M until an operator explicitly reviews
the actual provider/chain, complete fees and resource policy. No automatic increase.

For each policy2 review the service reads `eth_getBlockByHash` for the SAME
confirmed monetary snapshot, verifies hash/number/time and gasLimit, then uses
`min(operator_limit, confirmed_block_limit)`. Missing/malformed/inconsistent data
fails closed without a latest/number fallback or guessed zero. Per-transaction
and provider limits may be stricter; the operator must qualify those separately.
Both simulation and estimation use this effective cap. The complete20% estimate
headroom must fit; larger claim selections get smaller probes. Network fee,
balance, snapshot/expiry, bounded work/ingress and final review checks remain.

Policy2 emits unsigned draft/plan schema2 with configured/block/effective caps and
an identity-bound transaction policy hash. A matching consumer must explicitly
support it; do not silently pass it to a schema1 reviewer. No `gas`/nonce/signature
is inserted into the wallet transaction. The wallet still verifies latest state,
network, ownership, calldata, configuration, gas/fees and expiry before signing.
Existing served websites, shared Anvil-only signer and public DEPLOYMENT remain
unchanged. Backend source support alone is not consumer or production approval.

To change a reviewed running limit after sealing: reconcile pending transactions,
let outstanding reviews finish/expire, update the operator-owned policy file and
review hash, confirm matching consumer support, dry-run/restart the authorized
API workers, then verify schema/caps/configuration hash and exact simulations.
No on-chain governance setter is called. Do not change financial loss caps,
keeper gas limits or ProtocolPolicy internal-call budgets to accomplish this.
Keep the prior file for a reviewed rollback; old signed transactions still recover
by their saved hash. Publishing this procedure changes no actual configuration.

### Boundary with the 20M/24M qualification

The [controlled qualification](../reports/gas-profiles-20261113/REVIEW.md) supports
an explicit 20M **activation/growth** policy and separate 24M keeper/manual policies.
It does not select a higher mint/claim policy: transaction policy1 and checked-in
defaults remain 12M. Claim-policy2 adoption still requires its own exact policy,
consumer, workload and complete-fee review. Mint2/OpenSea selection is independent.

Activation/growth has a complete, separate `ActivationConfig` supplied through
`--activation-config`; this service uses `TransactionConfig` through
`--transaction-config`. They share an independently pinned read inventory, but
must run on separate listeners. Production worker admission rejects combining
the two policies. Never apply an activation schema/fee overlay to a claim file.

For source9/source10 **activation** reviews, the configured backend gas ceiling
must equal website `manifest.limits.gas` exactly; a 20M backend needs integer
`limits.gas:20000000`, explicit activation policy2 and matching activation/fee
identities. A lower confirmed-block effective ceiling does not permit a different
configured value. That activation ceiling can coexist with unchanged 12M claim
policy1. Both transaction APIs require full 20% policy2 estimate headroom; the
separate keeper/manual maintenance reviews retain 25% padding.

The qualification preserves financial, fee, funding, work and recovery checks.
It does not install a provider or approve target fees, live consumer admission,
hosted latency or maximum-state workloads. Use the
[operator procedure](OPERATOR_MANUAL.md#gas-profiles-20m-24m) for exact files,
ceilings, pending-first reconciliation, controlled restart and rollback; source
publication changes no running service or signer.

## Supported actions

| Action | Fixed target and call | Native value | Approvals |
| --- | --- | --- | --- |
| Historical mint integration1 dormant mint | Canonical Vault `mintDormant(expectedMintPolicy)` | Exact reviewed current mint price(default0.05ETH) | None |
| Explicit mint integration2 primary mint | Not prepared here: use the reviewed OpenSea/SeaDrop path | Free TEAM or reviewed AL/public gross price, gas separate | None |
| LP and royalty claims, mint integration1 or2 | Immutable NFT-owned router `claimBatch((uint256,address,bool)[])` | Zero | None |

Direct mint remains an implemented historical backend/Anvil capability, not the
fresh primary-sale path. With the Mint2 helper bound, direct paid Vault minting
cannot bypass SeaDrop. Historical mint1 provenance binds sale/VRF through
`mint_policy`; historical Anvil profiles retain their actual no-argument selector
and fixed terms.

The [SeaDrop Mint2 source](OPENSEA_MINT.md) implements dormant buyer issuance and
atomic gross/fee/net settlement. TEAM is free; AL/public use the reviewed governed
gross price(default0.05ETH), with gas separate. Actual custom-drop onboarding,
fees/payers, VRF and operating acceptance remain unqualified; source support is
not production approval. The website Mint page remains demonstrative.
Mint integration2 is independent of transaction gas policy1/2 and response
schema1/2: opting into V10 does not raise any gas/work budget, enable signing or
change an existing browser consumer. See [qualification](MINT_INTEGRATION_QUALIFICATION.md).

The service accepts only the connected wallet's public address and the typed
selection. Callers cannot provide RPC URLs, chain IDs, destinations, recipients,
arbitrary calldata, overrides, nonce, gas settings or spending approvals.
The service does not authenticate control of that address: only the wallet's
later signature and the contracts can authorize a transaction.

Claims contain 1-32 operations, not 32 NFTs times every asset. Each operation
names an actual decimal-string uint256 token ID, an admitted asset and a strict
boolean selecting royalties or LP rewards. Duplicate operations are rejected;
the same NFT/asset in the two different ledgers is valid. Native address zero is
allowed for royalties and, under explicit native accounting2–7, native LP rewards. The same NFT
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

The read configuration pins the canonical chain, deployment anchor, complete
selected contract/helper graph and admitted reward assets. Fresh7 also binds
LP-allocation1 and the immutable Rewards canonical companion; old6/V8 remains
a separate profile. The separate policy
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

Historical/default mint integration1 request (explicit2 rejects it):

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

The opt-in `POST /v1/claims/plan` accepts the same explicit claim payload.
It preserves every selected NFT/currency/ledger entry, tries bounded batch sizes
under the existing gas/fee/work policy and returns only `next_batch`, freshly
simulated through this preparer. Every selection remains in `entries`; blocked,
unresolved and nonzero omitted selections also remain in `remaining_claims`.
An opaque execution refusal does
not identify a malicious currency. No batch is signed, queued or sent. Confirm
the selected batch before planning the remainder against new state. See the
[complete planner contract](CLAIM_PLANNING.md). The existing prepare endpoint
continues to require the entire exact selected batch to succeed atomically.

Bracketed values are unusable examples, not configured accounts or addresses.
The endpoint requires one canonical Content-Length, at most 16 KiB, one expected
loopback Host and JSON content type. Duplicate JSON keys, transfer encoding,
malformed input and unexpected fields are rejected. There are no CORS grants,
request-body logs or upstream error disclosures. Typed input errors return 400,
unknown NFTs 404 for exact preparation, unavailable verification/simulation 503.
The planner instead returns an explicit blocked row for an unminted selection.
Work budgets and worker
supervision are implemented; public ingress, TLS, abuse limits and operating
qualification remain required before hosting.

## What a successful draft means

All state reads, simulation, gas estimation and wallet balance reads use **one
confirmed canonical block hash** with EIP-1898. The gas-price suggestion is a
preparation-time RPC quote, not a historical price. No `latest` fallback or state,
balance or allowance override. Historical mint1 preparation verifies the exact price, supply
cap, remaining supply, global pause, preparation mode and independent mint-pause
switch. Minting does not query unrelated reward currencies. Simulation exercises the actual mint,
VRF request and mint-recipient payment paths. Claims require the full reviewed
ledger inventory and core bindings, but isolate an unselected currency's failed
runtime/decimal check. Selected currency failures reject the whole draft;
terminal work limits are never swallowed. Actual simulation remains decisive.

For accounting3–7 claims, the preparer reads the global activation weight once per
distinct selected NFT at that same block. Only 0..3 is valid; weight0 plus a positive
LP/royalty claim balance is contradictory core data and rejects the draft. Missing
or malformed activation data also fails closed. This preserves the never-activated
reward invariant; it does not repeat the full NFT/traits/LP projection or add those
dependencies to claims. The weight is not used to calculate the payout. Activated parked/outbound NFTs
and optional-currency deferrals retain their earned rights. Historical profiles
do not acquire this getter requirement. No optional currency read is added merely
to check activation. [Scoped review](../reports/reward-resilience-20261026/REVIEW.md).

Accounting7 requires pinned `principal_exit` and custody5. Omitted/default mint
integration1 authenticates V9; explicit2 authenticates V10 plus the fixed
SeaDrop/helper bindings at that same block, without mutable sale/price checks
gating claims. Historical4
retains its own custody3/canonicalV5 profile. Its irreversible LP-exit flag blocks new mint and
activation/top-up drafts, including after unpause; earned LP/royalty claims stay
available to the current owner. Principal returns appear separately in read
responses and cannot be submitted as ClaimRouter reward operations. No backend
principal-payout draft endpoint or public signer is introduced. Historical1/2/3
readers and existing Anvil journals keep their original configuration. The served
poplint artifact remains its unconfigured accounting3 build until separately
reviewed; source publication changes neither that website nor its signer.

Claims use an exact, narrowly encoded array and an exact sender/value simulation.
Results must contain the canonical uint256 array offset, count and bounded size.
Returned `view_raw` and `simulated_raw` are separate raw token-unit strings.
Royalty synchronization or legitimate recipient callbacks can affect subsequent
operations during the simulated batch. Different assets are never added into
one dollar figure, and simulation is not a promise of a future payout.

Historical policy1 simulation and estimation retain a **12M gas work cap**. Estimates must be
21,000..12M; its suggested limit adds20% up to that cap. Explicit policy2 instead
uses its authenticated effective cap and requires full20% headroom as explained above. Gas price and
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

The selected read-service graph alone does not authenticate Entry, Registry, source
admission and dual Oracle policies. Activation requires those additional
reviewed identities, a complete original-source quote and a simulated marginal
LP deployment satisfying the captured contribution-loss budget. The current
ETH/fixed ZZZ candidate defaults to 3%, governed up to 10%, with its reviewed caller
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
VRF, hosting, actual OpenSea onboarding/fee/payer acceptance and independent
audit remain release gates.
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
