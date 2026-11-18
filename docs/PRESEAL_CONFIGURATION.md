# Unsigned fresh pre-seal configuration planner

`scripts/prepare-preseal.py` turns explicit reviewed inputs into a conditional,
ordered configuration review for the current schema17/mint2/V10/execution1/LP3
source. It uses the exact trusted `activation-final-six-20261118` build and current ABI.
Earlier pre-seal evidence retains its original metadata2 build/source scope;
the current Q03 family retains all seal guards while changing the royalty payload and execution implementation pins.
It performs **no RPC, simulation, signing, deployment, nonce reservation,
configuration adoption or sealing**. Existing contracts and environments stay.

This follows the [constructor reviewer](DEPLOYMENT_PREPARATION.md) and optional
[address/nonce planner](DEPLOYMENT_SEQUENCE.md). Those tools cover construction
and bindings; the new tool covers the subsequent twelve configuration families.
All are preparation, not authorization to submit transactions.

## Inputs and command

Copy [the null example](../config/preseal-preparation.example.json). Keep unknown
values null. JSON booleans must be `true`/`false`; ABI integers are canonical
decimal strings, without signs/leading zeros except signed values where allowed.
Code/review hashes use nonzero `0x` plus 64 hex characters. File SHA-256 values
use 64 hex characters without `0x`. Do not enter a key, RPC URL or keystore.

```sh
python scripts/prepare-preseal.py --input /review/preseal-input.json --output /review/NEW-preseal-review.json
```

The input is bounded to 64KiB; output to 16MiB, and each encoded call to64KiB.
These limits apply together. The output must be a NEW file in
an existing owner-controlled directory. Existing files, dangling entries and
collisions are preserved. The CLI rejects abbreviated/execution-related options
and sanitizes errors. A late publication error can leave complete unapproved
output: inspect and preserve it before using another fresh path.

| Field | Required meaning |
| --- | --- |
| `schema`, `profile`, `chain_id` | Exact example values: schema1, current source profile, chain4663. A historical build is rejected; no profile/source fallback. |
| `constructor_input` | Unchanged constructor-input schema: selected authorities/dependencies, assigned25top-level addresses, content and external review references. The existing constructor/build/source/ABI/normal-size checks run unchanged. Review digests are not independently verified by either tool. |
| `bootstrap` | Explicit public address of the actual Access constructor sender. Before seal, this is the configuration caller; governance is not automatically a substitute. Actual caller/control/code/canConfigure remain unverified. |
| `child_addresses` | Exact12constructor-helper roles from the example. Supply actual getter-derived addresses when known. Only a helper required as a call target blocks its own family/dependants; unused unknown children still require live graph verification. Never infer factory nonces or use zero as an unknown. |
| `settings` | The twelve fixed families below. Each family/object/field may remain null. Unknown own inputs or required preceding families block calldata. Unknown/extra fields reject. |

The tool accepts only this fresh, unsealed, zero-mint configuration phase. It is
not a partial-deployment/configuration resume tool. Inputs are unverified
assignments; they neither observe state nor prove any address is usable.

## Settings families and actual calls

The example expands nullable object fields. For list entries, use the field
names below or the source's `source_template()`, `pool_template()` and
`route_template()` helpers. Empty lists are deliberate choices, not unknowns.

| Family | Explicit inputs | Prepared calls / ordering |
| --- | --- | --- |
| `dual_usd` | `eth` and `zzz`: each `primary`, `secondary`, `maxDeviationBps`, `reviewHash`. Each source: `source`, `expectedCodeHash`, `independenceId`, `maxAge`, `feedDecimals`. | Two `Oracle.setDualFeed` calls. Distinct source addresses/IDs are required; IDs do not prove real independence. Source ages/decimals/agreement bounds are retained. |
| `fixed_zzz` | `expectedCodeHash`, `reviewHash` | `ActivationAssets.configureZZZ`, after feeds. Fixed ZZZ and declared hash must agree with the current Registry's immutable native profile. |
| `lp_asset` | `add_fixed_zzz:true` | `Rewards.addAsset(fixedZZZ)`. ETH is the existing native book; no third LP currency is added. |
| `migration_zzz` | `codeHash`, `reviewHash` | `Migration.configureZZZ`, matching Assets, Rewards and constructor-fixed Buyback ZZZ. No custody recipient/bridge is introduced. |
| `execution_sources` | `sources`: at most2 entries with `source`, `expectedCodeHash`, `reviewHash` | `Oracle.setExecutionSource(...,true,...)`. Each must match an admitted ZZZ primary/secondary and its pin. Enabled composite source precision must be18; its live interface/market remains unverified. |
| `native_pools` | At most4 entries: `config` plus `orientation:"1"` | `PoolRegistry.configureNative`, then **`Strategy.setRangeOrientation(poolId,1)` for that pool**. Admission alone leaves the old raw-ratio orientation. At most one contribution pool; its initial identity must be the selected ETH/ZZZ pool. |
| `routes` | `execution_pool_ids`, `execution_review_hash`, `conversion_routes`, `conversion_enabled` | Configure at most4 reviewed Balancer venues; add at most4 typed native-v4 fixed-ZZZ→ETH conversion routes; explicitly set converter enabled/disabled. Execution IDs must refer to admitted operations-enabled pools. No arbitrary router calldata or WETH/v3 path. |
| `confirmation` | `secondsRequired`, `maximumGap`, `reviewed`, `requireReferenceExit:true`, `referenceReview` | Configure confirmation and preserve independent same-side corroboration. A zero maximum gap means **stopped**, not a removed guard. No adaptive policy is enabled. |
| `randomness` | `coordinator`, `expectedCodeHash`, `keyHash`, `subscriptionId`, `confirmations`, `callbackGas`, `nativePayment`, `reviewHash` | `ProtocolPolicy.configureRandomness` with all8arguments. Initial pre-seal setup only; no provider rotation or pending-draw retargeting. |
| `seadrop_terms` | `artifact_path`, externally reviewed `artifact_sha256` | Load/rebuild the existing source-bound [OpenSea proof artifact](OPENSEA_MINT.md#prepare-the-plan-and-proofs-offline), match NFT/SeaDrop/payee/current initial0.05ETH price, then `SeaDropMint.configure`. The private file path is not copied into output. |
| `seadrop_upstream` | `publicKeyURIs`, `allowListURI`, `dropURI`; explicit EMPTY `existingFeeRecipients`, `existingPayers`, `existingSigners`, `existingTokenGated` | Fixed **NFT-forwarded** public-drop, allowlist, URI, payout, allowed-fee-recipient and payer updates. NFT is the target; the exact SeaDrop implementation is the first argument. Nonempty prior lists are unsupported fresh-state input, not automatically cleared. |
| `mint_end` | `end`, exactly matching the proof artifact's `publicEnd` | `NFT.setMintEnd` after terms/upstream review. It must still be in the future at inclusion. Royalty opening remains1hour after the official final end. |

Pool `config` contains `key` plus `depositsEnabled`, `operationsEnabled`,
`rangeBps`, `triggerBps`, `maxSpotDeviationBps`, `maxSlippageBps`,
`minRebalanceInterval`, `minDepositUSD`, `maxPositionUSD`. The key contains
`currency0`, `currency1`, `fee`, `tickSpacing`, `hooks`. Only native ETH/fixed
ZZZ, zero hooks, valid static fees/tick spacing and existing bounds are admitted.

Each conversion route contains `source`, `output`, `key`, `poolManager`,
`stateView`, `sourceCodeHash`, `outputCodeHash`, `poolManagerCodeHash`,
`stateViewCodeHash`, `reviewHash`. Output is native ETH with its exact marker;
fixed token/core/state pins must not contradict the Registry. Converter route
markets remain separate from principal custody pools.

The array bounds are finite **planner review-work bounds**, not new on-chain
lifetime capacities. URI strings are bounded to4KiB; the source-bound proof
artifact retains its existing8MiB limit. All stronger on-chain/user financial
guards still apply when a separately authorized operation executes.

## Results, deliberate stops and hashes

| Exit | Meaning |
| --- | --- |
|0 | Every family has enough consistent offline inputs to encode its conditional calls. All readiness/authority/runtime/approval flags remain false. |
|2 | A blocked preview was created. Inspect top-level and per-family `missing_inputs`; blocked calls have null calldata. No zero/default substitution. |
|1 | Invalid/unavailable input or uncertain publication; preserve existing/possibly complete output and inspect the exact reason. |

Each call records the fixed target role/address, explicit bootstrap, signature,
ordered typed arguments, zero ETH value and calldata. No gas/nonce/signature or
transaction envelope is prepared. The manifest pins producer sources, accepted
build/constructor review and used ABI definitions. Reusing shared native pin
constants adopts no historical validator, codec or deployment profile.

`manifest_sha256` is the canonical output fingerprint excluding that field.
It is **not** a contract `reviewHash`, `custodyHash` or permission. Review hashes
remain explicit operator-supplied evidence fingerprints; the contract does not
verify their preimages, and this tool does not invent missing hashes. The
OpenSea helper receives its separately rebuilt proof-manifest review hash.

`explicit_operating_stops` lists known deliberate stops: no execution venues,
conversion disabled, maximum observation gap0, no contribution destination,
or a pool with `operationsEnabled=false`. The latter names its exact pool ID
and stops contributions, compound and ordinary rebalance there; it does not
claim harvesting or earned-reward claims are disabled by that flag alone.
A complete static review can deliberately describe a stopped system. It never
means activation, maintenance or minting is ready. No automatic bypass/fallback,
unpause, relaxed source band, raised loss cap or adoption follows a tool result.

Constructor defaults are recorded, not changed: contribution3%, conversion1%,
maintenance3%, additional loss1%,85%position trigger, hybridOFF and adaptive
keeper rangeOFF. Explicit caller-selected bounded configuration is shown in the
call arguments. The approved human-price orientation is a real separate write;
it cannot be inferred from `rangeBps`.

## Before any later authorized execution

Independently reconcile actual chain, creation receipts, code/immutables/getters,
bindings, actual bootstrap/canConfigure, unsealed zero-mint graph, canonical
state and absence of preparation/exit. Confirm fresh empty upstream SeaDrop
lists, actual sale price/payee/root/payers/windows, and that `setMintEnd` remains
future at inclusion. Offline source review proves none of these live facts.

Qualify source independence/publication/liveness and fresh observations, live
token/dependency controls, usable pool/route depth, reference/venue compatibility,
VRF funding/consumer/callback, OpenSea onboarding, content, complete fees and
operating services. Simulate exact calls against actual state and review full
fees before separately authorizing execution. A real call may safely reject if
the state or market has changed; never compensate by bypassing safeguards.

Sealing and release sign-off remain separate. This tool emits no seal call.
Public signing stays disabled; existing Anvil, journals, sites/services and the
user-paused heartbeat remain unchanged. See the [source-scoped report](../reports/preseal-planner-20261116/REVIEW.md)
and [operator procedure](OPERATOR_MANUAL.md#prepare-unsigned-pre-seal-configuration).

The `seal_boundary_review` appendix covers all39 constructor instances and critical
chain/metadata/OpenSea/converter/venue/VRF/role/end/reservation reads. It remains
blocked pending actual observation and content review, even with complete offline
settings. Inert bytecode uses length/hash commitments, not duplicated full payloads.
See [irreversible setup](SEAL_READINESS.md); no seal calldata is generated.

## Launch royalty workload and gas reads

The [launch-workload review](../reports/launch-workload-20261117/REVIEW.md) supplies separate finite gas evidence. The unsigned planner now includes unverified `royalty_workload` and `gas_policy` rows. Read the actual royalty `assetCapacity()`, `assetCount()` and `assets(index)` for every zero-based uint256 index strictly below the observed count. Capacity16 permits16 ERC20s plus ETH; it does not imply they are already admitted. Read `ProtocolPolicy.gasPolicy()`, `royaltySyncGas()`, `sourceCallGas()`, `payoutGas()` and `gasFingerprint()` from the matching deployment.

Measure healthy, pending/initial-allocation and full-budget fault states for the actual list. A1M per-currency allowance is not a20M operation guarantee. Full20% activation-policy2/25% maintenance padding and actual service/block/complete-fee bounds remain;32M local diagnostics do not adopt a larger profile. All checklist flags stay false, and no RPC/configuration/seal call is added. Repeat reviewed workload qualification before later currency admission/capacity expansion.

The [current controlled workload](../reports/activation-final-six-20261118/REVIEW.md) passes all13 cold20M calls and their full20% padded calls; worst16,460,899 raw/19,753,079 padded. These exact tested inputs do not qualify another selected currency list, expanded64-currency/maximumLP2 state, target provider/fees or rollout. The planner still emits no signing, deployment or seal approval.

## Optional activation royalty-read allowance

Fresh payload6/allocation2, like explicit historical5, separates the activation-only ERC20 `balanceOf` cap (default50,000gas) from the unchanged full-sync allowance (default1M). Optional input `royalty_balance_policy:{"balanceGas":"50000","reviewHash":"REVIEW_HASH"}` prepares one separate exact unsigned `setRoyaltyBalanceGas(uint32,bytes32)` call after the original twelve families. Use a real nonzero bytes32 hash; unknown inputs remain blocked/null calldata and omission requests no write. Bounds10,000-1,000,000gas are engineering limits, not target-workload approval. Verify the actual cap/gas revision and requalify full healthy/faulted calls before adoption. No signing, submission, sealing or live approval is added.
