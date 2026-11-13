# Robinhood gas and RPC qualification

The [latest external qualification](../reports/predeployment-qualification-20261113/REVIEW.md)
now proves independently derived genesis and all13 existing RPC checks through
a paced helper call. Specific historical state/logs and tiny code-only override
simulation work. Full-work provider caps/plan, real financial inputs, exact current
launch-state operations and complete Nitro fees remain unqualified. No old gas
operation/test was repeated and no budget or provider is adopted.

This is an operator review procedure, not a deployment or provider-adoption instruction. Keep the activation/unsigned-review default of 12 million gas, the keeper's separate configured limits and the public signing restriction. Contract sealing does not change backend gas settings.

## Current evidence

The [current RPC/fee review](../reports/rpc-fees-20261113/REVIEW.md) finds a positive
tracing witness at the documented public Pinax endpoint
`https://robinhood.rpc.pinax.network`, chain4663. A discarded `approve(0)` call
returns the actual expected Approval log through unchanged `callTracer/withLog`
validation at a rechecked canonical hash. Cheap calls/estimates accept20M/24M
gas fields, and unknown hashes reject. This qualifies the observed interfaces,
not effective full-work gas capacity, archive reliability, a service plan or
production adoption. The later full-profile milestone is linked above.

The same campaign reads actual NodeInterface posting components for the ten
previously captured payloads, a complete harmless approval estimate and genuine
ordinary receipts. Posting fees are nonzero; earlier zero snapshots were not a
permanent waiver. PoPL itself is undeployed: these component observations do
not supply complete mainnet PoPL quotes or approve operator spending limits.

The [earlier read evidence](../reports/gas-feasibility-20261111/network/REVIEW.md)
establishes32M execution parameters despite the synthetic `1 << 50` header.
BlockVectra's public tier has a900-block history limit and rejects hash-state/
tracing; Daybreak accepts cheap hash calls but lacks tracing. Their failures
remain preserved, without weaker fallback or automatic provider adoption.

## Read the limits before choosing a budget

Use one recent numbered block, record its hash, read the precompiles at that block, and recheck the same header afterward. Complete the sequence within the provider's history window. Respect its request-rate limit; do not repeatedly retry access denials or a non-retryable history error.

These PowerShell examples use the public, uncredentialed candidate only. They do not change a service configuration and do not sign or send transactions:

```powershell
$publicRpc = 'https://robinhood.rpc.pinax.network'
cast chain-id --rpc-url $publicRpc
$anchor = cast block-number --rpc-url $publicRpc
cast block $anchor --json --rpc-url $publicRpc
```

Proceed only if the chain is 4663. Keep the returned anchor number and hash. Read the exact interfaces at `0x000000000000000000000000000000000000006c`:

```powershell
$gasInfo = '0x000000000000000000000000000000000000006c'
cast call $gasInfo 'getMaxTxGasLimit()(uint256)' --block $anchor --rpc-url $publicRpc
cast call $gasInfo 'getMaxBlockGasLimit()(uint64)' --block $anchor --rpc-url $publicRpc
cast call $gasInfo 'getGasAccountingParams()(uint256,uint256,uint256)' --block $anchor --rpc-url $publicRpc
cast call $gasInfo 'getPricesInWei()(uint256,uint256,uint256,uint256,uint256,uint256)' --block $anchor --rpc-url $publicRpc
cast block $anchor --json --rpc-url $publicRpc
```

These are command templates matching the published interfaces; they were not executed as a new test. The evidence campaign used equivalent bounded JSON-RPC calls. Compare both returned headers; reject an anchor mismatch or unavailable data. Do not substitute a later block silently.

| Item | What to check |
| --- | --- |
| Transaction execution parameter | Use the explicit getter, not header `gasLimit`. |
| Block execution parameter | Treat it separately from transaction allowance and pricing throughput. |
| Legacy accounting tuple | Exact reference implementation returns speed / block / block. The middle word is not a second transaction cap. |
| ArbSys version | Reference Nitro adds 55 to its internal version: observed 116 implies 61, not initial-config 51. |
| Pricing constraints | Targets/windows/backlogs influence pricing, not maximum transaction execution. |
| Provider gas ceiling | Obtain documented/reviewed call and estimate caps; a small getter succeeding proves neither. |
| Native fee quote | Separate pinned base fee, later gas-price read and complete-operation estimate. |

The [reference source and observed values](../reports/gas-feasibility-20261111/network/LIMITS.json) distinguish initial configuration, software documentation and live reads. A precompile/runtime code read alone does not prove all methods or versions: NodeInterface `0xc8` is virtual and may have no EVM code.

## Qualify the actual PoPL operation

1. Use the exact fresh runtime profile, source/configuration pins, entry calldata, representative state, assets, routes and feeds. A successful empty transfer or getter does not qualify activation, growth, claim, rebalance or exit.
2. Estimate/simulate the complete operation on the approved local fork and validate target execution/data-fee semantics. Do not deploy or submit a public transaction as part of this read-only procedure.
3. Keep the reviewed gas budget below the applicable live transaction/block execution parameters and provider caps; use a conservative gas-field ceiling no greater than the observed 32 million unless separately reviewed target semantics justify a different envelope. A synthetic header bound alone is insufficient.
4. Preserve full **20% headroom** for explicit activation/transaction policy2 and **25% padding** for keeper/manual LP maintenance reviews, reviewed network-fee ceilings, all financial guards and explicit matching consumers. Legacy policy1 keeps its original advisory-padding behavior. Do not raise a budget automatically when simulation fails.
5. Account for throughput: an expensive operation can consume a significant portion of block execution capacity. Multiple concurrent website users do not imply simultaneous chain inclusion. Qualify queueing, timeout, retry and recovery behavior separately.

Optional activation `schema:2` uses decimal-string `fee_policy.max_gas_limit` and `fee_policy.max_network_fee_wei`, with a matching website `activation_policy_schema:2` and reviewed configuration hash. The engineering maximum is not chain/provider approval. See [activation preparation](ACTIVATION_PREPARATION.md) and [operator settings](OPERATOR_MANUAL.md#unsigned-activation-gas-settings). Defaults stay unchanged; this guide does not install or adopt a new configuration. Preserve existing journals and pending operation identities through any later authorized rollout.

The explicit [20M/24M candidate package](../reports/gas-profiles-20261113/backend/profiles.template.json)
and [operator procedure](OPERATOR_MANUAL.md#gas-profiles-20m-24m) keep activation
and maintenance policies separate. Website `limits.gas` must equal the configured
activation ceiling exactly, even when the confirmed block imposes a smaller
effective cap. Null fee approvals and unsigned profiles are not deployable policy.

The [earlier provider review](../reports/gas-profiles-20261113/network/REVIEW.md)
retains the Daybreak/BlockVectra scope. The later
[Pinax witness and fee observations](../reports/rpc-fees-20261113/REVIEW.md) add
actual trace logs and fee-component evidence, without turning the earlier local
20M/24M estimates into complete target-chain quotes. Never estimate an empty
mainnet account at a recorded local Entry address and call that a PoPL result.
Verify deployed runtime/bindings and exact current operation state first.

## Calculate fees without double counting

Robinhood's [fee guide](https://docs.robinhood.com/chain/gas-and-fees/) and [Arbitrum estimation guide](https://docs.arbitrum.io/arbitrum-essentials/how-to-estimate-gas) describe a total estimate containing execution plus the L1 posting component expressed in L2 gas. For a provider confirmed to follow those semantics:

`estimated total ETH = complete estimated gas × reviewed wei-per-gas / 10^18`

Do not add the posting fee again to an already-inclusive estimate. NodeInterface
`gasEstimateComponents` returns total gas, posting gas, prospective L2 base fee
and estimated L1 price; total already contains posting. Its prospective price
can differ from the inclusion header or a later `eth_gasPrice`. The L1-only
method can inspect calldata without executing PoPL; it cannot provide the
missing full-operation execution estimate. Apply refreshed fee ceilings and
full20%/25% padding to a complete estimate. Neither the gas ceiling nor a local
benchmark multiplied by a live price guarantees final fees or inclusion.

Nitro may ignore priority fees. The observed nonzero-tip receipt pays only its
canonical base fee; using generic Ethereum base+tip would overstate daily spend.
The explicit future-only [zero-tip keeper profile](OPERATOR_MANUAL.md#robinhood-rpc-fees)
avoids that mismatch by requiring type2 with signed priority0. It does not
reinterpret existing pending fee reviews, approve a gas-price/day budget or
adopt a live provider. See the current report for exact source and receipt scope.

Provider rotation, budget changes and source publication require separate reviewed configuration/consumer adoption. They do not authorize public signing, deployment, service restart, existing Anvil changes or website rollout.
