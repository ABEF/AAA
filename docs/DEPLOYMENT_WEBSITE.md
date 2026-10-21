# Reviewed website API profile

The website now has a separate **read and unsigned-review profile** for the
existing production-shaped APIs. It is disabled in the shipped build:
`deployment-config.js` exports `DEPLOYMENT = null`. Public signing is absent from
this profile, and the existing browser signer still admits only the isolated
chain-31337 fixture. This is an integration candidate, not deployment approval.

See [verification](../reports/deployment-adapter/VERIFICATION.md),
[API hosting](API_INGRESS.md), [read API](FRONTEND_API.md),
[activation preparation](ACTIVATION_PREPARATION.md) and
[mint/claim preparation](FRONTEND_TRANSACTIONS.md).

## Data and action boundaries

| Website action | Source and behavior |
| --- | --- |
| Connect | Selected EIP-6963 provider (legacy fallback); public account authorization only. Multiple authorized addresses require selection. No private key, token approval, signature or network switch. |
| Restore | Deployment-specific tab storage plus `eth_accounts`; no permission prompt. A revoked address is not silently replaced by another. |
| My NFTs | Complete wallet-ID inventory, eight cards per page, at most two card projections in flight. Late account/page results are discarded. Each card shows its snapshot block. |
| LP attached | Confirmed `currentLPValue` projection in USD; unavailable values remain unavailable. An unsigned approval/contribution never changes the card or artwork. |
| Earnings | LP individual + collective + royalty earnings at current reviewed prices, only with matching NFT/block provenance. No price or matching history means unavailable, not zero. |
| ETH claim review | One to eight selected NFTs, funded ETH LP/royalty entries only. Source currencies are disclosed separately and are never relabeled ETH. |
| Mint review | Reconstructs `Vault.mintDormant()` and exactly 0.05 ETH. Minted count/control checks; no promised/reserved token ID. |
| Activation review | Token units from the reviewed Oracle, targeting exactly $100 in value with the smallest necessary raw-unit round-up. A changed price requires a new quote. |
| Growth review | User enters units of ETH/ZZZ/USDC/USDG, with a verified value of at least $5. Only reviewed enabled inputs/routes are accepted. |
| Approval review | Exact selected amount to the pinned Entry, never unlimited or a hidden zero-reset sequence. Complete preparation must run again after an actual confirmed approval. |
| LP execution review | Exact Entry calldata, selected NFT/pool/source/route, minimum output/liquidity and expiry; the backend trace must report at least 99% marginal LP deployed. Review displays simulated LP added and separate network gas. |
| Submit | **Unavailable.** No signing/submission method is implemented here. The preparation result is not a signable authorization. |

Wallet-page subtotals are deliberately absent: eight cards are not the entire
portfolio. Full collection aggregation is not wired in this candidate. The
ordinary overview artwork/examples remain educational examples, not live totals.
An account change invalidates a review; navigation closes it. Expiry is displayed
and a new review is required. There is no payment or approval retry path.

## Operator configuration

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
| `input_assets` | Up to four entries: `symbol` (ETH/ZZZ/USDC/USDG), `address`, `valuation_asset`, `decimals`, `route_id`, `enabled`, and ERC20 `runtime_code`. Native ETH uses address zero, 18 decimals and the reviewed native accounting asset for valuation. WETH is not a second input selector. |
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
   [wallet task](../TODO.md#task-wallet). Unknowns remain open.
2. Run the existing read/mint-claim and activation services under their reviewed
   configurations. Keep their independent admission, Origin and resource limits.
   Reverse-proxy GET `/api/v1/*` and POST `/api/v1/transactions/prepare` to the
   read/transaction service; POST `/api/v1/activation/prepare` goes to the
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
   public simulation. A non-null configuration enables reads/review, **not sends**.
   No server process, production RPC or public deployment is provisioned by the
   new adapter itself.

## Stop, diagnose and resume

- For stale/failed reads: refresh the same account; no write exists to retry.
  Error text is bounded/sanitized. Missing earnings do not erase known LP values.
- For a configuration/runtime/hash mismatch: stop preparation, investigate the
  reviewed deployment/service config and reissue a reviewed build. Never accept
  the changed target automatically or turn off identity checks to resume.
- For a missing/failed input route: disable that input in the operator manifest
  and follow the on-chain [asset/route procedure](OPERATOR_MANUAL.md#activation-assets-and-routes).
  Removing a selector does not itself revoke on-chain acceptance or old allowances.
- Roll back the static release atomically, or publish `DEPLOYMENT = null` to
  return to the simulation. Label it as simulation; never present its balances
  as confirmed state. No contract state is changed by this rollback.
- Preserve the existing local Anvil process, session and journals. Do not reset
  a chain to repair a website configuration/read failure.

The remaining signer extension must preserve explicit sender/network/genesis
checks, current re-simulation, exact approvals/calldata/gas, durable per-account
pending journals, canonical confirmation, replacement/reorg recovery and
confirmed-only LP/artwork updates. Automatic approval review rejected changing
the shared signer in this work because it could enable signing outside the local
profile. That change was not executed. It requires a separate explicit approval
and remains open, together with production qualification and independent audit.
