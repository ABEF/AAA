# Activation and top-up preparation

The backend prepares an **unsigned, fully simulated Entry transaction** for a
reviewed deployment. It does not sign, broadcast, approve a deployment or connect
the public website. The associated current-NAV guard and rebalance budget are described in [dynamic liquidity](DYNAMIC_LIQUIDITY.md). Qualification of
actual Robinhood routes, feeds, trace providers and network fees remains in
[the central task](../TODO.md#task-activation-quotes).

Fresh fee-quality source uses explicit `execution_quality_version:1` with actual
Strategy/Manager/helper capability/runtime/binding checks and observed policy
owner/revision at one canonical block. Historical absent/0 is not silently
upgraded. Quality RPC failure prevents a new guarded balance review; saved
receipt recovery and independent harvest retain their existing paths. An on-chain
cap setter needs no service restart, but a config/runtime/source rollout requires
the reviewed stop/reconcile/dry-run/restart procedure with journals preserved.
[Fee-adjusted scope and limits](EXECUTION_QUALITY.md).

## Current deployment and review profile

Fresh read configuration explicitly selects accounting6/fee-intake1 and the
complete [portfolio graph](POSITION_V6.md). Unsigned activation selects Entry
routing2/pricing2/review2, maintenance3/range1/LP-routing2/portfolio2/
confirmation3/execution-quality1. Pin Policy, Confirmation, Budget, Balancer,
math, typed LP child and actual core/periphery, including reciprocal module/parent
bindings. Fresh pins must match their corresponding parent read configuration.
No version field upgrades old contracts or grants signing permission.
Fresh LP-routing2 verification passes the configured `lp_position_executor`
binding into the actual execution observer; a present address alone is not
verification. Missing helpers, wrong parent/core/runtime and historical profile
substitution fail closed. [Actual verifier tests](../reports/day-audit-20261031/VERIFICATION.md)
exercise the full graph, not just configuration construction.

At one pinned canonical hash, authenticate both physical LP IDs, keys, owners,
ticks, liquidity and aggregate raw amounts. Value both legs at the captured
prices. Trace entrant funds through exact Manager→typed LP child→PosM calls;
initial activation creates main only, while growth increases only the existing
main. Existing residual/idle/compound remain in incumbent NAV but cannot pay an
entrant's marginal deployed-LP execution floor. Confirmed receipt/actual deployment
comes before shares, artwork or LP amount updates.

Preparation binds reviewed controls and portfolio geometry, distinguishes raw85%
need from600/300sampled readiness and hard cooldown, and does not promise keeper
inclusion time without real telemetry. A desired-disabled live residual is still
authenticated. Source checks240seconds and60–300jitter are service policy, not an
on-chain commitment that a user action will rebalance; contributions never recenter.

Historical accounting4 retains its separately selected maintenance1/2,
LP-routing0/1 and confirmation0/1/2 paths; historical3 and earlier retain their
own codecs. Fresh6 never falls back to those ABIs after an error. Legacy900-second
confirmation and old child creation rules are not the fresh profile.

Only native ETH and fixed ZZZ are original inputs; the two-source agreement
tolerance is3%, independently of loss budgets. Actual routes/feeds/trace providers
and website consumption remain unqualified. See [preflight](PRODUCTION_PREFLIGHT.md).

The parent read configuration requires the additional `principal_exit` runtime
pin. It must exactly equal the nested activation `migration` address/code hash;
this is an intentional alias, not another contract. Once `lpExitStarted` is true,
activation/growth drafts stop before approval, pricing or route work, including
after ordinary unpause. Existing profile3 deployments retain their old schema;
the served poplint artifact is not automatically upgraded or enabled for signing.

`executeReviewed(Request,maximumLossBps,expectedContributionPolicy)` encodes the review's captured current
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
| Original contribution value | Actual input amount and reviewed Oracle price/decimals, checked against `ActivationAssets.value`. Current accounting6 prices actual ETH directly at currency zero; historical profiles retain their original mapping. No assumed USD peg. |
| New deployed LP | The successful Entry/Vault execution's **marginal** deployment, taken from the fixed budget helper's accounting inputs. Incumbent liquidity, idle and compound cannot subsidize the new contribution. |
| New share issuance and LP units | Budget output and `SharesAdded`, cross-checked with the one LiquidityManager mint/increase and its PositionManager liquidity readings. Physical LP units belong to the shared pool; NFT shares are reported separately. |
| Network gas | A separate RPC estimate and observed gas price, with native-currency costs, suggested gas limit and a mandatory fee-policy review identity. It is outside the captured contribution execution limit (2% by default). |

Activation/growth minima default100/5USD and are governed for future contributions
through ProtocolPolicy; each is at least1USD and growth cannot exceed activation. The backend rejects below-floor requests before preparing approvals/traces.
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

The CLI loads the deployment, activation and request files as strict UTF-8 JSON
objects before constructing the projection/preparer or doing RPC work. Duplicate
fields (including escaped/nested keys), nonfinite numbers and nonobject roots
reject with the existing fixed failure message. A bad request cannot first start
pricing or preparation. Correct the private input explicitly; the tool does not
rewrite files, change approvals or retry a transaction. HTTP request validation
and all typed financial checks remain separate and unchanged.

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

Fresh activation uses a separate schema1 configuration with the exact fields below.
The parent read configuration is schema2 and explicitly selects
`accounting_version:6`, `fee_intake_version:1`, `protocol_policy_version:1` and the
complete source6 contract graph. Its required base fields are `schema`, `chain_id`,
`rpc_urls`, `deployment_block`, `deployment_block_hash`, `confirmations`,
`max_block_age_seconds`, `contracts`, `assets`; optional history/predecessor/royalty/
earnings sections retain their own exact schemas. See [read configuration](FRONTEND_API.md#deployment-configuration).

**Do not add `protocol_policy_version` to the activation configuration.** It
inherits authenticated Policy1 from Projection; an extra key is rejected. Both
configurations pin the same `protocol_policy` address/code hash and every other
shared role. `activation.contracts.migration` must equal the parent's
`contracts.principal_exit`. The parent has8 base roles, `principal_exit`, and14
source6 portfolio/policy/dependency roles; its23 bindings are not interchangeable
with the production inventory's17 modules/21 helpers.

Native ETH has address zero, code hash null,18 decimals and its own two-source
policy; on-chain admission uses `NATIVE_ASSET_CODE_HASH()`. Exact native value is
verified at Entry-to-Vault and Vault-to-manager boundaries, not only outside.

| Field | Fresh source6 contents |
| --- | --- |
| `schema` | Integer1. Missing/unknown/boolean versions and extra fields fail closed. |
| `routing_version`, `pricing_version`, `review_policy_version` | Explicit integers2,2,2. Reviewed Entry2 calldata includes `expectedContributionPolicy`. |
| `lp_routing_version` | Explicit2: authenticate Manager/Balancer, arithmetic and typed physical execution helpers and entrant-capped trace. |
| `portfolio_version` | Explicit2: authenticate PortfolioPolicy2 and configured main floor/gap with both physical legs. |
| `execution_quality_version` | Explicit1: authenticate Strategy ownership, additional-loss cap/MAX and monotonic revision. |
| `maintenance_policy_version` | Explicit3: configured85%-of-centre-to-boundary physical/reference condition or deliberate operator geometry update, with Strategy3/Budget4. |
| `rebalance_confirmation_version` | Explicit3: pinned matching confirmation child, range1/maintenance3/quality1, sampled600-second window/strict300-second maximum gap as selected policy; actual values are observed, not invented defaults. |
| `range_policy_version`, `range_policies` | Explicit1 plus a required list of `{pool_id,orientation,keeper}` covering every source pool. Manual ZZZ-in-ETH orientation and exact optional keeper policy are reviewed separately. |
| `contracts` | Exactly18 roles, each `{address,code_hash}`: `pools`, `oracle`, `liquidity`, `strategy`, `fees`, `membership`, `migration`, `entry`, `activation_assets`, `budget`, `v4_executor`, `contribution_pricing`, `balancing_router`, `portfolio_policy`, `lp_balance_math`, `lp_position_executor`, `protocol_policy`, `rebalance_confirmation`. Shared pins must equal the parent read configuration. |
| `tokens` |2..33 reviewed currency descriptors, at most32 ERC20s plus ETH. Fields: `address`, `code_hash`, `decimals`, `price_policy`; original input, pair currencies and required historical backing must be covered. This inventory does not admit new contribution inputs. `price_policy` has `policy_id`, `ordinal`, `policy`; policy fields are `token`, `primary`, `secondary`, `maxDeviationBps`, `assetDecimals`, `reviewHash`. Each source has `source`, `expectedCodeHash`, `independenceId`, `maxAge`, `feedDecimals`; decimals0..18 and age1..86400seconds. Native code hash is null/decimals18; no single-feed fallback. |
| `dependencies` |1..64 `{address,code_hash}` entries covering PositionManager, PoolManager, StateView, Permit2 and every applicable conversion router/factory/pool, sequencer, implementation or other reviewed dependency. The four venue pins must equal the parent's exact dependencies. |
| `sources` |1..64 `{pool_id,source_asset,route_id,asset_policy_id,route_kind}` entries; one route per input/pool. Kind0 direct,1 v3,2 v4. Inputs must contain only native ETH and exactly the fixed reviewed ZZZ. Zero route is direct; nonzero native-source conversion requires v4. |
| `sequencer` | `{address,policy_id}` exactly matching Oracle. Explicit zero/zero only when that absence was reviewed; no implicit omission. Nonzero sequencer needs its dependency code pin. |
| `call_pins` | Up to128 `{target,data,expected}` exact getter checks on reviewed contracts, tokens, feeds or dependencies. Include applicable implementation/admin policy. |
| `storage_pins` | Up to64 `{target,slot,expected}` exact32-byte storage checks. Include applicable proxy implementation/admin/beacon slots and implementation code pins. |
| `fee_policy` | `{estimate_includes_all_fees:true,review_hash,max_gas_price_wei}`. Positive bounded decimal-string gas ceiling; independent review must establish complete network-fee estimation. No missing-component zero fallback. |

Historical accounting4 keeps its explicit maintenance1/2, LP-routing0/1 and
confirmation0/1/2 shapes; accounting5 keeps Portfolio1/Entry-review1 with its own
pins. Those configurations are not source6 templates and are never promoted
by omitting fields, changing version labels or falling back after an error.

Configuration hashes are returned in provenance. Runtime hashes alone cannot
establish a usable swap. LP2 `provenance.lp_execution` reports the bounded
catalog/revisions/work settings; `swaps_enabled` means its list is nonempty,
not that a listed venue is currently executable. Full simulation and on-chain
output/LP guards decide that. The catalog is not frozen by a wallet review.
Runtime hashes alone cannot
prove an upgradeable dependency's implementation/admin policy: review and specify
its relevant getter/storage pins, including feed proxies. Changing a source
policy, route, implementation, feed or fee model requires fresh review and config.
Unsupported fee models need another reviewed estimator, not a fabricated zero
for L1/data fees. The backend does not infer Robinhood support from generic EVM
compatibility. Suggested gas cost is an estimate, not a maximum final receipt fee.

## Confirmed range and timing context

Fresh source6 uses maintenance3/confirmation3/Portfolio2. The main may still be
active when its configured centre-to-boundary threshold is crossed. Physical
pool and independent reference must confirm the same threshold side; the
600-second sampled window, strict300-second maximum gap and hard cooldown are
distinct. The service checks every240seconds; execution additionally awaits its
persisted60–300-second random delay and financial/custody checks.

`rebalance.eligibility_rule` is `confirmed_threshold_or_operator_geometry_update`;
`eligibility_reason` is `threshold_distance`, `operator_geometry_update` or null.
`raw_eligible_at_snapshot` and confirmed `eligible_at_snapshot` remain separate.
The report includes actual main/residual geometry, current policy fingerprint,
physical/reference threshold sides, sampled status and the cooldown boundary.
`next_keeper_check_at`/`expected_execution_at` remain null without qualified
telemetry: no sampled countdown promises transaction inclusion. Deliberate
operator geometry updates retain their explicit cooldown-gated exception.

The following compatibility labels belong to explicitly historical profiles;
they are not the source6 decision rule.

### Historical timing labels

`liquidity_context` accompanies both approval and full Entry drafts. It contains
current/proposed ticks, current physical LP ID, active-range status and the
strategy's observed rebalance state. `earliest_eligible_at` is the cooldown
end, not a promised execution. The warning includes this timestamp or "eligible
now"/"waiting for actual range exit or operator range update" in policy2;
historical policy1 retains its original movement label. `next_keeper_check_at` and
`expected_execution_at` remain null without qualified operating telemetry.
No fabricated 10-minute countdown is emitted. See [timing rules](DYNAMIC_LIQUIDITY.md#admission-and-rebalance-timing).

With confirmation1/2, `rebalance.raw_eligible_at_snapshot` reports the raw candidate
and `rebalance.eligible_at_snapshot` reports confirmed readiness. The separate
`rebalance_confirmation` object exposes policy, first/last samples, side/identity,
remaining seconds and readiness at that block. The status distinguishes
unconfigured, not started, stale, confirming and ready; a late observation or
changed side/identity must restart. A deliberate governed range change bypasses
the sampled window after the existing raw cooldown/price checks. A countdown is
not a service schedule or proof of continuous price history. Historical confirmation2
also reports the reference policy and physical/reference sides; a coherent
disagreement is `reference_disagreement`, not ready. Independent-source/provider
qualification remains separate from internally consistent observations.

`rebalance.range_update_pending` also reports a governed range mismatch. Policy2
`eligibility_reason` is `range_update`, `out_of_range`,
`out_of_range_and_range_update` or null; historical policy1 retains
`price_trigger`/`price_and_range`. The reason describes the candidate even during
cooldown and does not itself authorize execution. Reads use one canonical hash. The pinned
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
and [sole Todo](../TODO.md). The fresh confirmation/schema6 additions have
[separate scoped verification](../reports/practical-improvements-20261028/VERIFICATION.md);
they do not requalify those historical providers or the served poplint artifact.

## Accounting6 policy binding

Projection requires protocol_policy_version1 and its reviewed helper/runtime.
The activation subsection pins the same helper but does not accept a duplicate
protocol_policy_version key. Entry2 calldata includes the exact captured
entryFingerprint after the maximum loss field; source minima and entrant idle cap
are dynamic at the pinned block. Stale policy or mid-call changes revert; no
legacy Entry selector is substituted. [Policy semantics](ADAPTABLE_POLICY.md).
