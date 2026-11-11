# Robinhood gas and RPC qualification

This is an operator review procedure, not a deployment or provider-adoption instruction. Keep the activation/unsigned-review default of 12 million gas, the keeper's separate configured limits and the public signing restriction. Contract sealing does not change backend gas settings.

## Current evidence

The [11 November read-only report](../reports/gas-feasibility-20261111/network/REVIEW.md) found a working anonymous mainnet candidate at `https://api.blockvectra.com/v1/robinhood_mainnet/public`. Chain ID was 4663. At block 111632516 the ArbGasInfo transaction and block execution parameters were **32 million gas** each, despite the header advertising the synthetic Nitro `1 << 50` gas limit. A later selected-core runtime hash matched the Registry pin. This is limited read evidence, not approval for production or complete PoPL transaction acceptance.

The provider's [public catalog](https://api.blockvectra.com/v1/chains) advertised 3 requests/second, burst 20, batch 10 and only 900 recent blocks. An actual old-anchor read failed with `-32011 state_window`. The public tier is unsuitable for lifetime event/history replay. Its numerical call/estimate gas cap and sustained availability remain unqualified. [Published endpoint documentation](https://docs.blockvectra.com/en/guides/robinhood-chain/) distinguishes mainnet 4663 from testnet 46630.

## Read the limits before choosing a budget

Use one recent numbered block, record its hash, read the precompiles at that block, and recheck the same header afterward. Complete the sequence within the provider's history window. Respect its request-rate limit; do not repeatedly retry access denials or a non-retryable history error.

These PowerShell examples use the public, uncredentialed candidate only. They do not change a service configuration and do not sign or send transactions:

```powershell
$publicRpc = 'https://api.blockvectra.com/v1/robinhood_mainnet/public'
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
4. Preserve full **20% headroom** for activation/unsigned reviews, the keeper's separate **25% padding**, reviewed network-fee ceilings, all financial guards and explicit matching consumers. Do not raise a budget automatically when simulation fails.
5. Account for throughput: an expensive operation can consume a significant portion of block execution capacity. Multiple concurrent website users do not imply simultaneous chain inclusion. Qualify queueing, timeout, retry and recovery behavior separately.

Optional activation `schema:2` uses decimal-string `fee_policy.max_gas_limit` and `fee_policy.max_network_fee_wei`, with a matching website `activation_policy_schema:2` and reviewed configuration hash. The engineering maximum is not chain/provider approval. See [activation preparation](ACTIVATION_PREPARATION.md) and [operator settings](OPERATOR_MANUAL.md#unsigned-activation-gas-settings). Defaults stay unchanged; this guide does not install or adopt a new configuration. Preserve existing journals and pending operation identities through any later authorized rollout.

## Calculate fees without double counting

Robinhood's [fee guide](https://docs.robinhood.com/chain/gas-and-fees/) and [Arbitrum estimation guide](https://docs.arbitrum.io/arbitrum-essentials/how-to-estimate-gas) describe a total estimate containing execution plus the L1 posting component expressed in L2 gas. For a provider confirmed to follow those semantics:

`estimated total ETH = complete estimated gas × reviewed wei-per-gas / 10^18`

Do not add the posting fee again to an already-inclusive estimate. A separate component estimate is for reconciliation. Apply the actual fee envelope/ceilings and refreshed state; the formula is not a guarantee of final charged gas or inclusion. The November 11 snapshot's zero L1 price estimate is not a permanent guarantee. No complete PoPL target-chain fee quote was produced by that read-only campaign.

Provider rotation, budget changes and source publication require separate reviewed configuration/consumer adoption. They do not authorize public signing, deployment, service restart, existing Anvil changes or website rollout.
