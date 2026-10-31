# Reviewed website API profile

The website has disabled-by-default read and unsigned-review adapters. Public
`deployment-config.js` exports `DEPLOYMENT = null`; nonlocal submission is
unavailable, and the shared signer remains Anvil-only.

## Deployment compatibility

| Profile | Scope |
| --- | --- |
| Historical schema 1 | Wrapped-asset/single-feed local deployments, original 1% contribution policy and original journals |
| Historical schema2/native2 | Accounting2, dual pricing2, routing2 and reviewed Entry2; see [preserved native2 manifest](NATIVE_WEBSITE_PROFILE.md) |
| Served schema3/accounting3/localV4 | [Explicit current3 reader/unsigned-review profile](CURRENT_WEBSITE_PROFILE.md), served separately through poplint; actual reviewed contracts/API/providers remain unconfigured/unqualified |
| Fresh accounting6/custody4/portfolio2/canonical V6 contracts | Backend read/unsigned adapters authenticate both physical legs and full helper/core graph. A compatible deployed website consumer is still pending; add/review its explicit profile before connecting these contracts, never relabel schema3 or old journals |

The legacy configuration and local-wallet procedures below retain their own
profile scope; they are not instructions to configure fresh6. Native2 supports a captured governed contribution cap;
the schema 1 99% fixture floor is not a universal current rule. The contract
candidate accepts ETH/fixed ZZZ only and defaults to 2% contribution loss; manifest
input admission, code/runtime pins and quote policy must match the selected
version exactly. No source publication updates a static server, existing chain,
wallet journal or running service.

See [verification](../reports/deployment-adapter/VERIFICATION.md),
[API hosting](API_INGRESS.md), [read API](FRONTEND_API.md),
[activation preparation](ACTIVATION_PREPARATION.md) and
[mint/claim preparation](FRONTEND_TRANSACTIONS.md).

## Confirmed collection explorer

The reviewed profile now lists the canonical collection and complete current LP
total without connecting a wallet. Search, eligibility/rarity/color/style filters,
16-row pages, current-LP/newest sorting and read-only current-owner details are
implemented. Unknown marks remain unavailable. Deploy matching API/proxy/frontend
versions and follow [the collection read procedure](COLLECTION_READS.md). Public
DEPLOYMENT stays null; this does not enable signing or qualify live hosting.

## Data and action boundaries

| Website action | Source and behavior |
| --- | --- |
| Connect | Selected EIP-6963 provider (legacy fallback); public account authorization only. Multiple authorized addresses require selection. No private key, token approval, signature or network switch. |
| Restore | Deployment-specific tab storage plus `eth_accounts`; no permission prompt. A revoked address is not silently replaced by another. |
| My NFTs | Complete wallet-ID inventory, eight cards per page, at most two card projections in flight. Late account/page results are discarded. Each card shows its snapshot block. |
| LP attached | Confirmed `currentLPValue` projection in USD; unavailable values remain unavailable. An unsigned approval/contribution never changes the card or artwork. |
| Earnings | LP individual + collective + royalty earnings at current reviewed prices, only with matching NFT/block provenance. No price or matching history means unavailable, not zero. |
| ETH claim review | One to eight selected NFTs, funded ETH LP/royalty entries only. Source currencies are disclosed separately and are never relabeled ETH. |
| Mint | Production: demonstration only; mint preparation blocked pending qualified OpenSea integration/URL. Local rehearsal retains `Vault.mintDormant()` with exactly 0.05 ETH. See [mint qualification](MINT_INTEGRATION_QUALIFICATION.md). |
| Activation review | Token units from the reviewed Oracle, targeting exactly $100 in value with the smallest necessary raw-unit round-up. A changed price requires a new quote. |
| Growth review | Historical manifests may expose ETH/ZZZ/USDC/USDG units. Served current3 restricts contributions to ETH/fixed ZZZ and a verified $5 minimum. Fresh4 needs its own compatible profile with the same fixed contribution identities. |
| Approval review | Exact selected amount to the pinned Entry, never unlimited or a hidden zero-reset sequence. Complete preparation must run again after an actual confirmed approval. |
| LP execution review | Exact Entry calldata, selected NFT/pool/source/route, minimum output/liquidity and expiry; the trace must meet the selected version's captured marginal-LP floor. Legacy schema 1 uses 99%; native2 uses its reviewed governed cap. Show simulated LP added and gas separately. |
| Submit | Nonlocal: unavailable. Local Anvil rehearsal: explicit wallet confirmation, independent preflight, same-hash recovery and confirmed-state reconciliation through the unchanged signer. |

Wallet-wide LP and claimable ETH totals aggregate every holding in bounded
16-item chunks at one canonical block. Card pagination never becomes a total.
Missing/incomplete data remains unavailable. Historical current-holdings earnings
use separately reconciled 16-NFT chunks at the same block. Collection holder
allocations consume the existing earnings endpoint; full collection inventory/LP
aggregation uses the separately checked collection source. See [definitions and operations](EARNINGS_HISTORY.md#current-holdings-totals). The
ordinary overview artwork/examples remain educational examples, not live totals.
An account change invalidates a review; navigation closes it. Expiry is displayed
and a new review is required. There is no automatic payment or approval retry. Local recovery only reads the saved transaction.

## Legacy schema-1 operator configuration

Use a separately reviewed build configuration, committed with its deployment
evidence. Never accept an RPC, contract, route, policy or manifest from a URL
parameter, localStorage, extension name, API auto-discovery or user input. No
production values have been selected or inferred by this implementation.

`deployment-config.js` accepts either `null` or a plain object with these fields:

| Fields | Required meaning |
| --- | --- |
| `schema`, `mode`, `environment` | `1`, `read-and-prepare`, and `production` or `rehearsal`. No signing flag exists. |
| `id` | Reviewed 64-character lowercase hexadecimal deployment identity; connection storage is isolated by this value. |
| `chain_id`, `chain_name` | Independently verified integer chain ID and display name. Production rejects 31337. |
| `genesis_hash`, `deployment_block`, `deployment_block_hash` | Exact independently checked chain/genesis and immutable deployment anchor. |
| `confirmations`, `max_age_seconds` | Required depth (1-128) and maximum snapshot age (1-120 seconds). These are confirmation policy, not a finality proof. |
| `rpc_url` | Public HTTPS node, no credential/query/fragment. HTTP is admitted only for explicit literal-loopback rehearsal. The node is used for independent read verification, never signing. |
| `api_prefix` | Same-origin path such as `/api`, without trailing slash. No cross-origin API discovery. |
| `projection_sha256`, `transaction_sha256`, `activation_sha256` | Exact identities from independently reviewed read, mint/claim and activation service configuration. |
| `transaction_fee_review`, `activation_fee_review` | Reviewed complete-network-fee policy hashes, including applicable chain-specific fee components. |
| `contracts` | `access`, `nft`, `vault`, `entry`, `claim_router`, `oracle`; each has exact lowercase `address` and full `runtime_code`. Never substitute a mock or proxy implementation without reviewing the boundary. |
| `pool_id` | The one currently admitted contribution pool. Switching pools requires matching on-chain, API and website review; no arbitrary user pool selection. |
| `input_assets` | Up to four entries: `symbol` (ETH/ZZZ/USDC/USDG), `address`, `valuation_asset`, `decimals`, `route_id`, `enabled`, and ERC20 `runtime_code`. The existing website profile uses zero input plus a nonzero legacy valuation asset. Use the separate schema-2 native profile for V2 zero-asset valuation; do not deploy a V2 backend under this old manifest. WETH is not a second input selector. |
| `reward_assets` | Exact admitted currency address/symbol/decimals inventory. A new or changed currency cannot silently reuse an old label/precision. |
| `limits` | `gas` integer plus decimal-string `gas_price_wei`, `network_fee_wei`, `native_value_wei`, `contribution_usd_18`. These are hard preparation bounds, not approval of public spending. |

Production profiles require an HTTPS website. Rehearsal profiles require an
HTTP `127.0.0.1` website. Configuration errors disable the profile rather than
falling back to simulated balances. The existing launcher's `/app/` loopback
profile ignores this configuration and retains its own local wallet admission.

## Hosting and rollout

1. Qualify the real deployment, Oracle/feed freshness, token/runtime/route
   inventory, fee semantics and RPC hash selectors first. Read the
   [production services record](PRODUCTION_SERVICES.md) and the central
   [wallet task](../TODO.md#task-wallet). Select a frontend profile that actually
   supports that contract version. Fresh4 support remains open; native2/current3
   builds cannot be made compatible by changing a version field.
2. Run the existing read/mint-claim and activation services under their reviewed
   configurations. Keep their independent admission, Origin and resource limits.
   Reverse-proxy only the enumerated reviewed GET routes and exact POST
   `/api/v1/transactions/prepare` to the read/transaction service; POST `/api/v1/activation/prepare` goes to the
   activation service. Strip only `/api`; do not expose service control paths.
3. Configure browser `connect-src` for the exact reviewed node plus same-origin
   API. The node must support browser CORS and canonical hash reads. Never put
   a provider secret into the public manifest; use a reviewed constrained read
   gateway if needed. Do not weaken the current public site's policy in advance.
4. Build with reviewed configuration in an isolated rehearsal. Verify real
   accounts, stale/failed feeds, currency outages, account revocation, API errors,
   exact unsigned payloads and current simulation results. The committed fixtures
   verify interfaces only; they do not qualify live services or extensions.
5. Publish only the approved static build. `DEPLOYMENT = null` preserves the
   public simulation. A non-null production configuration enables reads/review, **not sends**. A literal-loopback Anvil rehearsal can enable the local wallet coordinator below.
   No server process, production RPC or public deployment is provisioned by the
   new adapter itself.

## Stop, diagnose and resume

- For stale/failed reads: refresh the same account; no write exists to retry.
  Error text is bounded/sanitized. Missing earnings do not erase known LP values.
- For a configuration/runtime/hash mismatch: stop preparation, investigate the
  reviewed deployment/service config and reissue a reviewed build. Never accept
  the changed target automatically or turn off identity checks to resume.
- For a fresh accounting6/portfolio2/holder-exit deployment: stop at the unsupported-profile
  boundary until its frontend is implemented and qualified. Do not substitute
  a schema3 manifest, historical API or example data to make the site load.
- For a missing/failed input route: disable that input in the operator manifest
  and follow the on-chain [asset/route procedure](OPERATOR_MANUAL.md#activation-assets-and-routes).
  Removing a selector does not itself revoke on-chain acceptance or old allowances.
- Roll back the static release atomically, or publish `DEPLOYMENT = null` to
  return to the simulation. Label it as simulation; never present its balances
  as confirmed state. No contract state is changed by this rollback.
- Preserve the existing local Anvil process, session and journals. Do not reset
  a chain to repair a website configuration/read failure.

## Local API wallet rehearsal

On 2026-10-21 the user chose to retain the shared signer's local Anvil restriction.
The proposed nonlocal signer change was rejected by automatic approval review and
was not applied. This local-only alternative leaves BrowserWallet/BrowserClient
unchanged. Public signing is not enabled or authorized by this implementation.

Use an isolated reviewed configuration with `environment: rehearsal`, chain 31337,
and an HTTP literal `127.0.0.1` page and RPC. All existing deployment, runtime,
route, fee, provenance and lifecycle pins are still required. The shared signer
supports at most 32 confirmations. Do not populate this manifest from an arbitrary
query, wallet or unreviewed API response. Current public config remains null.
The existing `/app/` launcher and its stored NFTs/journals are a separate profile;
this change does not restart, reset or reconfigure it.

1. Connect the intended wallet and select an authorized account. Reads/restoration
   never prompt a signature. An explicit **Switch to [reviewed chain name]** button
   requests a switch, then verifies the chain and genesis. Unknown networks require
   the operator's independently reviewed settings; no guessed RPC is auto-added.
2. Prepare a typed action. The coordinator reads the pending nonce and presents
   exact calldata/value/gas from the verified API review. Confirm explicitly in the
   selected wallet. Runtime pins, current simulation, permission, chain/genesis,
   nonce, funds and spending limits are checked again before the single send.
3. ERC20 approval is exactly the selected amount. On confirmation the same dialog
   prepares the complete LP execution and requests a second explicit confirmation.
   Approval never changes LP/artwork. If the new review still requests approval,
   stop and explain the changed allowance/amount; never chain another approval.
   Native ETH needs only the Entry transaction. An existing sufficient allowance
   also needs only execution. A changed price may require a fresh $100 quote.
4. The same account/genesis journal and cross-tab lock prevent duplicate sends.
   Rejection clears only the unsent operation. Unknown submission/receipt errors
   keep recovery. If the wallet lost its hash response, copy its activity hash into
   recovery; the signer independently checks exact sender/nonce/calldata/value/fees.
   Never erase a journal or repeat a confirmed approval to bypass an error.
5. A confirmed receipt and an API outage are different states: **Confirmed - balances
   catching up** retains the confirmed journal for read-only recovery. Fresh API
   provenance must reach the receipt's block. LP activation/growth also requires
   exactly one matching Entry `SourceContributed` event, confirmed active NFT shares
   and an available LP valuation. Refresh holds back only that pending contribution's
   artwork/LP; claims do not mark artwork pending. Market value need not increase by
   the contribution amount if prices moved; actual execution is evidenced separately.
6. Failed on-chain execution is reported as reverted, with network gas potentially
   spent. A canonical failed receipt can be acknowledged without a working API.
   Successful claims may already have new income; never demand a zero balance.
   Network/account changes invalidate unsent reviews and preserve saved operations.
   Return to the original account/deployment to recover its transaction.

Speed-up/cancel replacement-hash discovery is still open: do not clear the original
journal or silently accept a different hash. Preserve evidence for operator review.
Actual MetaMask/Rabby acceptance, real API hosting, routes, pricing, fees and
production capacity still require qualification. [Focused evidence](../reports/deployment-local-wallet/VERIFICATION.md)
uses mocked providers and real Python response fixtures; it is not a live-chain test.

The implementation follows the [EIP-1193 provider/account-event boundary](https://eips.ethereum.org/EIPS/eip-1193)
and [explicit chain-switch method](https://eips.ethereum.org/EIPS/eip-3326).
See also [network-addition semantics](https://eips.ethereum.org/EIPS/eip-3085) and
[canonical transaction/receipt RPC fields](https://ethereum.org/developers/docs/apis/json-rpc/).

## Queued or changed transaction numbers

Recovery now checks the submitted transaction before waiting for inclusion.
A changed nonce, a non-executable predecessor queue on the reviewed node, or a
consumed nonce without its receipt returns a specific diagnostic immediately.
Recover status reads the same hash; repeated clicks do not repair a wallet queue.
Close remains available and does not cancel or erase the transaction.

Keep the original review/hash. Check the selected network/genesis, wallet activity,
transaction/receipt and latest/pending account nonces. A missing hash is unresolved,
not proof that nothing was sent. Never auto-resend, clear pending storage, fill
nonce gaps with payments or reset the chain. Local MetaMask activity can outlive
a disposable development chain; only after separately reconciling pending sends
should its documented local activity/nonce reset be considered. That reset does
not cancel a signed transaction on a node. Public-wallet cancellation/replacement
reconciliation is not implemented here. See
[scoped diagnosis and evidence](../reports/browser-wallet/PENDING_NONCE.md).

## Actual local API integration

The historical [local API rehearsal](LOCAL_API_REHEARSAL.md) records real Anvil receipts
and real API worker responses. Its market/feed/VRF boundaries remain local mocks;
actual extension acceptance remains open. No nonlocal signing was added.
