# Robinhood mainnet: read-only gas and provider evidence

Baseline `db509fbf4e357e5aec1d614ce66923fea0594d7e`; observed 11 November 2026. No contract, site, service, signer, configuration, financial safeguard or default gas limit changed. Public signing remains disabled. This report qualifies bounded public reads, not deployment or production operation.

## Working anonymous provider

A mainnet candidate works at `https://api.blockvectra.com/v1/robinhood_mainnet/public`, published in the [provider guide](https://docs.blockvectra.com/en/guides/robinhood-chain/) and [chain 4663 registry](https://raw.githubusercontent.com/ethereum-lists/chains/master/_data/chains/eip155-4663.json). All seventeen initial requests returned valid matching JSON-RPC results, not merely HTTP 200. A subsequent five-read fresh identity check also succeeded. No account, key or funds were used.

The gas anchor is **111632516**, hash `0x420f9a45ce0d7fadcda1a4f126f6dd17e2c1c3099432eafd156ca38baf3c5a50`, **10:29:47 UTC**, rechecked unchanged after the precompile reads. A separate identity anchor is **111634609**, hash `0xa22edc32d6ac30c01417d464b0cf8bdd14e8d5360fd6458b98853de354ee56b2`, **10:33:26 UTC**, also rechecked. Its selected Uniswap core is 24,009 bytes; Keccak `0xbd3881180b547f5fe817545743cfb4343e96b1bc6640dcd70c106b0066e95626` matches baseline `src/ZZZPoolRegistry.sol:170`. This corroborates known code; it does not prove provider honesty or independently finalized state.

The provider's [live public catalog](https://api.blockvectra.com/v1/chains) advertises **3 requests/second**, burst 20, maximum batch 10, one public in-flight request per instance and **900 blocks of recent history**. The attempted November 9 anchor and the gas anchor revisited minutes later returned valid RPC error `-32011 state_window`; those failures are preserved. This public tier cannot provide PoPL's archival history workload. Its catalog gives no numerical `eth_call`/`eth_estimateGas` gas ceiling. Successful small views do not qualify a 15–19 million gas operation.

## Effective limits versus header accounting

At the pinned gas anchor, ArbGasInfo returned:

| Read | Result | Interpretation |
| --- | ---: | --- |
| `getMaxTxGasLimit()` | 32,000,000 | Stored transaction execution limit parameter |
| `getMaxBlockGasLimit()` | 32,000,000 | Stored block execution limit parameter |
| `getGasAccountingParams()` | 7,000,000 / 32,000,000 / 32,000,000 | Legacy speed / per-block / per-block |
| Header `gasLimit` | 1,125,899,906,842,624 | Synthetic Nitro `1 << 50`, not execution capacity |
| `arbOSVersion()` | 116 | Raw interface value; reference offset 55 implies internal 61 |

The [documented node image](https://docs.robinhood.com/chain/run-a-full-node/) is Nitro `v3.11.2-3599aca`; exact source and dependency commits are in [LIMITS.json](LIMITS.json) and [SOURCES.json](SOURCES.json). Its [ArbSys implementation](https://github.com/OffchainLabs/nitro/blob/3599acae1ad2fab4059fc46453c9cd3294126641/precompiles/ArbSys.go#L66) adds 55 to the internal version. The [initial published configuration](https://cdn.robinhood.com/assets/generated_assets/hoodchain_docsite/chain-node-configs/robinhood-chain-info.json) says 51; that initial setting is not the observed live version. The provider's current binary/commit was not established.

In that exact reference release, [ArbGasInfo](https://github.com/OffchainLabs/nitro/blob/3599acae1ad2fab4059fc46453c9cd3294126641/precompiles/ArbGasInfo.go#L160) returns the per-block limit twice in its legacy tuple. Its [transaction processor](https://github.com/OffchainLabs/nitro/blob/3599acae1ad2fab4059fc46453c9cd3294126641/arbos/tx_processor.go#L620) treats the newer transaction parameter as an execution limit after data charging and intrinsic accounting. These mutable state parameters are distinct from the synthetic header. Thus 32 million is useful feasibility evidence, not proof that the provider accepts a 32 million `gas` field or that the full candidate operation succeeds.

A roughly 18 million reviewed operation also represents substantial execution against a 32 million block parameter. Do not translate concurrent browser users directly into immediate transaction throughput. Nitro reservation, refund and inclusion behavior still needs exact-operation qualification.

The separate pricing-constraints getter returned targets of 60 million gas/second over 15 seconds and 15 million gas/second over 86,400 seconds, with observed backlog 6,103,394 each. These govern pricing/throughput, not transaction maxima. Legacy 7 million/second is not substituted for those constraints. Header gas used was 37,533; captured fee-history ratios were all 1. These ratios do not establish use of the synthetic header capacity.

## Fees: observed numbers and missing operation quote

Pinned header base fee was **20,132,000 wei/gas (0.020132 gwei)**; minimum was 20,000,000 wei. The later, unpinned `eth_gasPrice` read was **20,080,000 wei/gas (0.02008 gwei)**. They describe different moments. ArbGasInfo returned zero for its L1 price estimate/calldata component at this snapshot; this is not a promise of permanently free posting. All six prices and four-block fee history are retained in [LIMITS.json](LIMITS.json).

Robinhood's [fee documentation](https://docs.robinhood.com/chain/gas-and-fees/) and [Arbitrum estimation guidance](https://docs.arbitrum.io/arbitrum-essentials/how-to-estimate-gas) explain that ordinary total gas estimates bundle execution and L1 posting gas. **Do not add the posting component twice.** Multiplying a local fixture cost by a snapshot gas price is a conditional projection, not a complete target-chain quote. No candidate estimate, NodeInterface component estimate, signed transaction or public receipt was produced here.

ArbSys/ArbGasInfo code reads were `0xfe`; virtual NodeInterface `0xc8` returned `0x`. No code at this RPC-only interface does not establish unavailability; its estimate methods were not called. The documented 96 KiB code / 192 KiB initcode settings were not tested live. Project 24/48 KiB gates remain unchanged.

## Preserved failures and remaining qualification

Official RPC, PublicNode, dRPC and BlockReq each returned explicit Cloudflare 1010 access denial on their first read. They were not retried, spoofed or accessed with alternate signatures. An earlier restricted-network attempt failed locally with `URLError`. Blockscout reads returned 403 too. These are access failures for this client, not evidence of a chain-wide or provider-wide outage. Some provider articles were visible through the research tool while direct script article GETs returned 403; [SOURCES.json](SOURCES.json) separates those scopes.

The campaign made **31 RPC attempts: 23 valid results, 3 explicit RPC errors, 4 HTTP access denials and 1 local network failure**. Raw captures stay external with hashes; [OBSERVATIONS.json](OBSERVATIONS.json) publishes sanitized summaries, preserving unsuccessful results. No unchanged tests were repeated.

Still required: exact fresh-candidate full-operation estimation/execution on an authorized local fork with target gas semantics; provider numerical gas-cap, retention and sustained-availability qualification; independently corroborated anchors; reviewed RPC/fee/time budgets and full 20% headroom; real market/feed/VRF/OpenSea/authority qualification; operating recovery and independent audit. Discovering this endpoint changes no production configuration and raises no default.
