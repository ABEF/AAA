# Activation and top-up preparation

The backend prepares an **unsigned, fully simulated Entry transaction** for a
reviewed deployment. It does not sign, broadcast, approve a deployment or connect
the public website. The associated current-NAV guard and rebalance budget are described in [dynamic liquidity](DYNAMIC_LIQUIDITY.md). Qualification of
actual Robinhood routes, feeds, trace providers and network fees remains in
[the central task](../TODO.md#task-activation-quotes).

## Current deployment and review profile

The read configuration selects accounting 4 / fee-intake 1; deployment checks
require direct governance 2, custody3 and holder-exit canonical V5. Activation uses explicit
routing 2 / pricing 2 / review policy 1. These are separate version fields,
not a synthetic service-profile string or an upgrade of an existing deployment.
Accounting4 activation configuration also requires explicit
`maintenance_policy_version`:1 for historical movement eligibility,2 for current
outside-or-operator-range eligibility. Policy2 requires range_policy_version1,
authenticates Strategy2 and Budget3 at the pinned hash, and reports actual
outside state with obsolete movement-trigger fields null. Missing/malformed
capabilities fail closed; keeper check/execution times remain unavailable without
real telemetry. No historical deployment is upgraded by changing a field.
Only native ETH and fixed ZZZ are original inputs. Their two-source policies
use the reviewed 3% disagreement tolerance.

The parent read configuration requires the additional `principal_exit` runtime
pin. It must exactly equal the nested activation `migration` address/code hash;
this is an intentional alias, not another contract. Once `lpExitStarted` is true,
activation/growth drafts stop before approval, pricing or route work, including
after ordinary unpause. Existing profile3 deployments retain their old schema;
the served poplint artifact is not automatically upgraded or enabled for signing.

`executeReviewed(Request,maximumLossBps)` encodes the review's captured current
contribution cap. Responses expose `reviewed_maximum_loss_bps`, actual
`execution_limit_bps` and `provenance.review_policy_version`. A later cap above
the signed maximum rejects; a tighter policy remains binding. Default
contribution loss is 2%, conversion 1%, maintenance 3%, each with a 10% hard
maximum and network gas separate. No fallback to an old Entry selector occurs.

Preparation uses profile-specific dormant status 3 for the current code and 5
for explicit historical profiles; growth requires Active 1. Native zero is a
typed currency argument, never a contract target or owner. Existing deployments,
journals and historical ABI readers keep their original profile.

Historical non-current compound is included only in incumbent share pricing.
The trace parser authenticates the exact current bucket-bearing Budget result
frame, with separate explicit historical decoding. Same-block token/dual-price
review is required for nonzero historical backing; it never satisfies a new
contribution's marginal deployed-LP floor. See [price security](PRICE_SECURITY.md).

## Values returned to the wallet

| Value | Source and meaning |
| --- | --- |
| Current attached LP value | `NFT.currentLPValue(tokenId)` at the confirmed block: the NFT's share of marked deployed LP, attributed idle and compound reserves. It is not lifetime deposits, a withdrawal entitlement or claimable fees. Unavailable valuation is `null`, never an invented zero. |
| Original contribution value | Actual input amount and reviewed Oracle price/decimals, checked against `ActivationAssets.value`. Current accounting 4 prices actual ETH directly at currency zero; historical profiles retain their original mapping. No assumed USD peg. |
| New deployed LP | The successful Entry/Vault execution's **marginal** deployment, taken from the fixed budget helper's accounting inputs. Incumbent liquidity, idle and compound cannot subsidize the new contribution. |
| New share issuance and LP units | Budget output and `SharesAdded`, cross-checked with the one LiquidityManager mint/increase and its PositionManager liquidity readings. Physical LP units belong to the shared pool; NFT shares are reported separately. |
| Network gas | A separate RPC estimate and observed gas price, with native-currency costs, suggested gas limit and a mandatory fee-policy review identity. It is outside the captured contribution execution limit (2% by default). |

Activation requires at least $100 original input value; increases require at least
$5. The backend rejects below-floor requests before preparing approvals/traces.
The effective minimum also respects any higher pool `minDepositUSD`. Entry and
the fixed Vault helper enforce the same floors, including direct Vault calls.
See [contribution minimums](CONTRIBUTION_MINIMUMS.md) for configuration and evidence.

At the current 2% default, a $5 top-up requires at least $4.90 of new LP;
a $100 original contribution requires at least $98 of marginal deployed
LP. The floor rounds up in raw USD units, as in the contract. Idle input is not
counted as deployed LP. The NFT's existing marked value can change with prices;
do not calculate its new total by adding the contribution to lifetime deposits.
LP/royalty claim balances remain separate. The website still shows examples.

## Preparation sequence

1. Accept only a typed current-owner request. Pin one recent confirmed block hash
   with `requireCanonical`; verify the deployment anchor, sealed module/helper
   bindings, canonical lifecycle, NFT identity/reveal, custody and pool state.
2. Verify reviewed runtime hashes, asset admission policy, append-only route ID,
   venue identity, feed/decimal/age configuration, current Oracle prices,
   sequencer policy and configured dependency getters/storage slots.
3. Check actual balance and Entry allowance. An insufficient ERC20 allowance
   returns one exact replacement approval draft even for a smaller nonzero
   allowance. Tokens requiring a separate zero reset fail simulation and are
   unsupported by this two-transaction flow. Simulate and estimate that approval; **no activation quote is
   declared ready**. After confirmation, prepare again. No unlimited approval,
   fabricated allowance, permit, arbitrary recipient or arbitrary calldata.
4. Simulate the complete original-source conversion, balancing and LP addition
   using the built-in `callTracer` with logs. Check original input, helper result,
   share event and actual liquidity delta. The internal probe is never returned
   for signing and still executes the contract's captured deployed-LP floor.
5. Derive conversion-output and liquidity minima using the requested 0..1000 bps
   tolerance. This only supplies additional output/LP minima; it cannot relax the
   captured contribution floor or stronger venue guards. Resimulate **exactly the calldata returned to the wallet**. Economic
   outputs must agree at the same snapshot; gas may differ with calldata.
6. Estimate gas at that same hash; verify native balance, price/gas ceilings and
   final canonical hash, chain, confirmation depth, deployment anchor and age.
   Return a short-lived draft only while its deadline remains valid.

Both approval previews and complete Entry reviews validate the contribution
pool's existing slot0 response. Typed v4 input routes apply the same validation
to their own pool: canonical integer ABI fields, initialized TickMath bounds,
`sqrtAtTick(tick) <= sqrtPriceX96 <= sqrtAtTick(tick + 1)`, each packed 12-bit
directional protocol fee at most 1,000 pips, and a stored LP fee matching the
reviewed static PoolKey fee. Contradictory state fails closed. The inclusive
upper endpoint preserves v4's real downward-crossing boundary state; active-range
membership uses the stored tick, never a substituted floor tick. This reuses
already-required pinned reads and adds no request/response fields or RPC calls.

The outer Entry deadline is on-chain for activation/top-ups; an ERC20 approval
has no on-chain expiry. Snapshots must be at most 120 seconds old and cannot be
more than 30 seconds in the future; draft lifetime is at most 60 seconds and never
extends past the snapshot age limit. Requests and traces are bounded. Providers
without hash-pinned tracing/logs/estimation fail closed; there is no `latest`,
state-override or conversion-only fallback.

## Running the local service

Both commands require the existing schema-2 [read-service configuration](FRONTEND_API.md)
and a **separate reviewed activation configuration**. Paths are relative to the
checkout or may be absolute; no production manifest is supplied by this example.

```text
python -m frontend_api.activation --config deployment.json --activation-config activation.json --request request.json
python -m frontend_api.activation_server --config deployment.json --activation-config activation.json --port 8788
```

The opt-in HTTP process binds only to `127.0.0.1`. `POST /v1/activation/prepare`
accepts the same flat request as the CLI. The normal read service stays GET-only.
The separate saved mint/claim POST candidate is not required by this service.
Bodies are limited to 16 KiB; duplicate JSON/header fields, alternate framing and
unknown fields are rejected. Errors omit upstream exception text and credentials.
No signer or broadcast method is exposed.

```json
{
  "action": "activate",
  "wallet": "<current owner address>",
  "token_id": "<canonical decimal token ID, not mint ordinal>",
  "pool_id": "<reviewed 32-byte pool ID>",
  "source_asset": "<reviewed token address; zero address for native ETH>",
  "amount_in": "<positive raw integer amount as a string>",
  "slippage_bps": 50
}
```

Use `increase` for top-ups to the NFT's current pool. Configuration and request
examples deliberately contain placeholders, not purported live addresses.

## Activation configuration schema 1

The current profile requires the base fields and explicit version fields below;
additional or missing fields are rejected. Historical profiles have their own
exact shape, not null placeholders for newly required fields.

Use current accounting 4 / fee-intake 1 in the parent read configuration. The
nested activation schema remains 1. Native ETH has address zero, code hash null,
18 decimals and its own two-source policy; on-chain admission uses
`NATIVE_ASSET_CODE_HASH()`. Exact ETH value is verified at Entry-to-Vault and
Vault-to-manager boundaries, not only on the outer transaction.

| Field | Contents |
| --- | --- |
| `schema` | Integer `1`. |
| `routing_version`, `pricing_version`, `review_policy_version` | Explicit integers `2`, `2`, `1` for this candidate. |
| `contracts` | Exactly `pools`, `oracle`, `liquidity`, `strategy`, `fees`, `membership`, `migration`, `entry`, `activation_assets`, `budget`, `v4_executor`, `contribution_pricing`; each has `address` and `code_hash`, distinct from the read-service's eight bindings. |
| `tokens` | 2..33 reviewed currency descriptors, at most 32 ERC20s plus ETH. Current fields: `address`, `code_hash`, `decimals`, `price_policy`; input, pair currencies and required nonzero historical backing must be present. `price_policy` contains `policy_id`, `ordinal`, `policy`. The policy includes `token`, `primary`, `secondary`, `maxDeviationBps`, `assetDecimals`, `reviewHash`; each source includes `source`, `expectedCodeHash`, `independenceId`, `maxAge`, `feedDecimals`. Token/feed precision is 0..18 and source age 1..86400 seconds. Native code hash is null and decimals 18. No legacy single-feed keys in pricing 2. |
| `dependencies` | 1..64 `{address, code_hash}` entries covering PositionManager, PoolManager, StateView, Permit2 and every applicable conversion router/factory/pool, sequencer, implementation or other reviewed dependency. |
| `sources` | 1..64 `{pool_id, source_asset, route_id, asset_policy_id, route_kind}` entries. One route per input/pool: kind 0 direct, 1 v3, 2 v4. For fee-intake 1, source identities must contain native ETH and exactly one reviewed ZZZ; no third input. Zero route is direct; nonzero native-source conversion requires v4. |
| `range_policy_version`, `range_policies` | Optional explicit range profile 1 adds a required list of `{pool_id, orientation, keeper}` reviewed policies covering every source pool. Its absence/profile 0 retains the explicit historical raw-direction interpretation; it does not verify a newer range policy. See [range policy](RANGE_POLICY_UPDATES.md). |
| `sequencer` | `{address, policy_id}` exactly matching Oracle. Explicit zero/zero only when that absence was reviewed for this network; no implicit omission. |
| `call_pins` | Up to 128 `{target, data, expected}` exact getter checks on pinned contracts, tokens, feeds or dependencies. Include implementation/admin or wrapper policy getters where applicable. |
| `storage_pins` | Up to 64 `{target, slot, expected}` exact storage checks; 32-byte words. Include applicable proxy implementation/admin/beacon slots and pin the implementation code in dependencies. |
| `fee_policy` | `{estimate_includes_all_fees: true, review_hash, max_gas_price_wei}`. The ceiling is a positive decimal string. The review must establish that `eth_estimateGas * eth_gasPrice` covers all network fee components for this network/provider. |

Configuration hashes are returned in provenance. Runtime hashes alone cannot
prove an upgradeable dependency's implementation/admin policy: review and specify
its relevant getter/storage pins, including feed proxies. Changing a source
policy, route, implementation, feed or fee model requires fresh review and config.
Unsupported fee models need another reviewed estimator, not a fabricated zero
for L1/data fees. The backend does not infer Robinhood support from generic EVM
compatibility. Suggested gas cost is an estimate, not a maximum final receipt fee.

## Confirmed range and timing context

`liquidity_context` accompanies both approval and full Entry drafts. It contains
current/proposed ticks, current physical LP ID, active-range status and the
strategy's confirmed rebalance eligibility. `earliest_eligible_at` is the cooldown
end, not a promised execution. The warning includes this timestamp or "eligible
now"/"waiting for price trigger"; `next_keeper_check_at` and
`expected_execution_at` remain null without qualified operating telemetry.
No fabricated 10-minute countdown is emitted. See [timing rules](DYNAMIC_LIQUIDITY.md#admission-and-rebalance-timing).

`rebalance.range_update_pending` also reports a governed range mismatch.
`eligibility_reason` is `range_update`, `price_trigger`, `price_and_range` or null;
it describes the observed trigger even during cooldown. Eligibility is checked
against both triggers and cooldown at the same canonical hash. The pinned
Strategy must expose the matching `rangeUpdatePending(uint256)` getter; invalid
or missing responses fail closed. See [range updates](RANGE_POLICY_UPDATES.md).

Outside-range and rebalance-due contributions remain allowed under the existing
price/cost/custody guards. Before signing, reprepare after a physical position,
range or relevant policy change; the transaction has economic minima/deadline,
not an on-chain physical-LP version lock. The schema-2 read response additionally
returns `position.local_custody` (current pool/LP ID and share denominator) and
`cumulative_gross_contribution_usd_18`; neither historical input nor pending fees
may replace `current_lp_value`. Unavailable marks stay null.

## Wallet and operating boundary

Wallet code must independently verify chain/account, deployment and exact typed
calldata; discard drafts after owner/network/configuration changes or expiry;
repeat live simulation and gas estimation immediately before user signing.
Approval confirmation requires a new activation request. Handle rejected/replaced
transactions and canonical receipts/reorgs, and refresh the NFT's on-chain value
after confirmation. Smart-account execution/fee sponsorship is not qualified by
an EOA-style call simulation. The loopback server now uses [bounded parallel workers](CONCURRENT_SERVICES.md)
and ingress/work deadlines; overload returns 503 `service_busy` with Retry-After.
Hosting still needs reviewed ingress/origin/rate policy, health/error monitoring
and actual provider/operating qualification.

RPC traces are observations from the configured provider, **not cryptographic
execution proofs**. Reviewed code and the on-chain checks enforce the limit when
the eventual transaction executes; state changes can make it revert and consume
gas. The backend cannot guarantee execution or remove oracle/governance/venue risk.

Geth documents the [built-in call tracer and logs](https://geth.ethereum.org/docs/developers/evm-tracing/built-in-tracers)
and [hash-selected debug calls](https://geth.ethereum.org/docs/interacting-with-geth/rpc/ns-debug).
Local compatibility evidence is in the [scoped verification](../reports/activation-preparation/VERIFICATION.md);
it does not qualify a hosted production RPC or an actual ETH/ZZZ route. Current
feature evidence and remaining gates are maintained in the [feature reference](IMPLEMENTATION_STATUS.md)
and [sole Todo](../TODO.md).
