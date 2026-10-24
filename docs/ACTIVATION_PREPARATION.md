**Current policy, 2026-10-24:** [Typed v4 conversions](TYPED_V4_ROUTES.md) and
[governed execution-loss limits](EXECUTION_LOSS_POLICY.md) are implemented in the
undeployed candidate. Defaults are 2% contribution, 1% conversion and 3% maintenance;
immediate governance may set each category up to a hard 10%. Existing stricter
venue/caller minima remain. Pending normal custody approvals retain their original
absolute floor. Earlier fixed-cap or v3-only descriptions below retain their
historical/default scope. Actual routes, services and independent audit remain open.

# Activation and top-up preparation

## Composed-bucket share pricing - 2026-10-23

The current Budget result call includes the exact bucket ID. The parser supports
that eight-argument signature and the explicit historical seven-argument signature;
unknown/ambiguous calls fail. Historical compound Oracle.value calls are read only
from the current result frame, verified against reviewed same-block token/feed
pins and included in incumbent share pricing. They never satisfy new input's
captured marginal-deployed floor (98% at the current 2% default). Missing historical token/price review refuses a draft.
Legacy local deployments remain readable; public response shape, exact approvals,
unsigned preparation and Anvil-only signing policy are unchanged. See
[verification scope](../reports/pair-composition/VERIFICATION.md).

The backend prepares an **unsigned, fully simulated Entry transaction** for a
reviewed deployment. It does not sign, broadcast, approve a deployment or connect
the public website. The associated current-NAV guard and rebalance budget are described in [dynamic liquidity](DYNAMIC_LIQUIDITY.md). Qualification of
actual Robinhood routes, feeds, trace providers and network fees remains in
[the central task](../TODO.md#task-activation-quotes).

## Values returned to the wallet

| Value | Source and meaning |
| --- | --- |
| Current attached LP value | `NFT.currentLPValue(tokenId)` at the confirmed block: the NFT's share of marked deployed LP, attributed idle and compound reserves. It is not lifetime deposits, a withdrawal entitlement or claimable fees. Unavailable valuation is `null`, never an invented zero. |
| Original contribution value | Actual input amount and reviewed Oracle price/decimals, checked against `ActivationAssets.value`. Native V2 prices actual ETH directly at currency zero; historical V1 retains its wrapper mapping. No assumed stablecoin peg. |
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
5. Derive conversion-output and liquidity minima using the requested 0..100 bps
   tolerance. Resimulate **exactly the calldata returned to the wallet**. Economic
   outputs must agree at the same snapshot; gas may differ with calldata.
6. Estimate gas at that same hash; verify native balance, price/gas ceilings and
   final canonical hash, chain, confirmation depth, deployment anchor and age.
   Return a short-lived draft only while its deadline remains valid.

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

All top-level fields below are required; additional fields are rejected.

The parent read-service configuration explicitly selects `accounting_version: 2`
for native deployments and verifies Vault version2 and the V2 canonical schema.
The nested activation schema number stays1. Native V2 permits32 ERC20s plus ETH
(`address: zero`, `code_hash: null`, decimals18, independently pinned ETH feed).
Native admission uses `NATIVE_ASSET_CODE_HASH()`, not a WETH runtime. Legacy V1
configuration remains separate. Exact ETH value is checked on Entry-to-Vault and
Vault-to-manager calls, not only on the outer transaction.

| Field | Contents |
| --- | --- |
| `schema` | Integer `1`. |
| `contracts` | Exactly `pools`, `oracle`, `liquidity`, `strategy`, `fees`, `membership`, `migration`, `entry`, `activation_assets`, `budget`; each has `address` and `code_hash`. These are distinct from the read-service's eight bindings. |
| `tokens` | 2..32 ERC20 objects in V1; V2 permits those32 plus one native ETH entry. Fields: `address`, `code_hash`, `decimals`, `feed`, `feed_code_hash`, `feed_decimals`, `max_age`. Input and both accounting currencies must be present; decimals0..18, age1..86400 seconds. Native code hash is null and decimals are18. |
| `dependencies` | 1..64 `{address, code_hash}` entries covering PositionManager, PoolManager, StateView, Permit2 and every applicable conversion router/factory/pool, sequencer, implementation or other reviewed dependency. |
| `sources` | 1..64 `{pool_id, source_asset, route_id, asset_policy_id}` entries. One selected route per input/pool; zero route is direct/native input. Native V2 uses zero source and its explicit native policy; V1 retains the original wrapper policy. |
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
it does not qualify a hosted production RPC or an actual stable-to-Pons route.
