# Requested Robinhood ETH / ZZZ pool

The user selected this market for future PoPL liquidity. Its identity and fee policy were checked on **2026-10-14** with read-only public RPC requests and verified source. No transactions were sent. The current PoPL contracts do not support this native-ETH, hooked LP pool. The later creator-payment receiver is a separate funding path; it does not change the read-time market verification below.

## Network and pool identity

[Robinhood's network documentation](https://docs.robinhood.com/chain/connecting/) lists mainnet chain ID **4663**, native currency **ETH**, and public RPC `https://rpc.mainnet.chain.robinhood.com`. [Uniswap's deployment table](https://developers.uniswap.org/docs/protocols/v4/deployments) lists the Robinhood PoolManager and StateView below.

| Field | Verified value |
| --- | --- |
| Pool ID | `0x6538e2c223ed70228114983afecbe5e69fe627e2fafdf367bdd6bdeff2ad391f` |
| PoolManager | `0x8366a39cc670b4001a1121b8f6a443a643e40951` |
| StateView | `0xf3334192d15450cdd385c8b70e03f9a6bd9e673b` |
| `currency0` | `0x0000000000000000000000000000000000000000` — native ETH, not WETH |
| `currency1` | `0x7dbf38976f6D3b9c529e7D9484A71898B409eE6a` — ZZZ |
| `fee` | `0` — 0% core LP fee |
| `tickSpacing` | `200` |
| `hooks` | `0xE5e702641Ea86F4ae6cC3cDaeD2B886f976Be044` |
| Hook identity | Explorer-verified `PonsV2MemeHook`, displayed as V2MemeHook |
| ZZZ metadata | `symbol() = "ZZZ"`, `decimals() = 18` |

The PoolManager's `Initialize` event in [transaction `0x699e86e0b41888308103b7f2fc09a9c269b5bf01c4369cfffaafaaf798977ba5`](https://robinhoodchain.blockscout.com/tx/0x699e86e0b41888308103b7f2fc09a9c269b5bf01c4369cfffaafaaf798977ba5), block **54,672,541**, supplies this PoolKey. Hashing `abi.encode(currency0, currency1, fee, tickSpacing, hooks)` independently reproduced the exact requested pool ID. `StateView.getSlot0(poolId)` returned both core `protocolFee = 0` and `lpFee = 0` at the verification reads.

The pool can be viewed in [Uniswap](https://app.uniswap.org/explore/pools/robinhood/0x6538e2c223ed70228114983afecbe5e69fe627e2fafdf367bdd6bdeff2ad391f); the token is [ZZZ on Uniswap](https://app.uniswap.org/explore/tokens/robinhood/0x7dbf38976f6D3b9c529e7D9484A71898B409eE6a).

## Core LP fees and Pons hook revenue are different

The core pool charges no swap fee for ordinary LP positions. Its hook takes a separate trading fee through `afterSwap`. Adding liquidity to this pool does not give the PoPL project a proportional claim on that hook's revenue.

The hook's pool-specific `launches(poolId)` getter returned:

| Policy field | Value at verification |
| --- | --- |
| `hookFeeBps` | `100` — 1% |
| `creatorTaxBps` | `0` — no additional creator tax |
| `protocolFeeShareBps` | `3000` — Pons receives 30% of the base hook fee |
| `buybackBurnBps` | `5000` — configured slice of the post-protocol creator bucket when enabled |
| `buybackEnabled` | `false` |
| Creator payout recipient | `0x698084856F65Bf1B4740E3D0dBA0B57A5B1deBA9` |
| Pons protocol payout recipient | `0x263ed295dAFaE1d9AAdD6E56c4B6F9f38eE019Dd` |
| Fee escrow | `0xd3AFEB2a57f70eF218Aa82451c51B2fb0416Ac9e` |
| Hook factory | `0x7eD598BcEf8bd9Edd8C97A195C6d13f40801EC7e` |

With buybacks disabled, newly collected base hook fees are split 70% to the creator and 30% to Pons, after conversion and rounding. Recipient and buyback settings are snapshots of the verification reads, not a promise that adjustable settings remain unchanged.

The hook charges 1% of the swap's **unspecified currency**: the output for an exact-input swap or the input for an exact-output swap. Accrued launch-token fees may later be converted to the quote currency before payout. An estimate based on dollar volume alone therefore cannot establish exact collected revenue. Read `HookFeeCollected` and `PoolFeesSwept` events for actual amounts and distinguish their currencies and conversion timing.

[Pons v2's own documentation](https://docs.ponsfamily.com/v2#uniswap-v4-pools) explains the zero core fee, hook collections, and recipient-based distribution. The [verified hook source](https://robinhoodchain.blockscout.com/address/0xe5e702641ea86f4ae6cc3cdaed2b886f976be044?tab=contract) was obtained through the explorer's [legacy source-code API](https://robinhoodchain.blockscout.com/api?module=contract&action=getsourcecode&address=0xe5e702641ea86f4ae6cc3cdaed2b886f976be044). Its `_afterSwap` and `_distribute` functions implement the described charging and payout rules.

## PoPL LP integration and creator payments

The current PoPL registry and liquidity adapter reject native currencies and nonzero hooks. Registering a pool ID does not add native settlement, hook handling, or revenue entitlement. Conventional ERC20/ERC20, hookless static-fee pools remain the supported candidate boundary.

The current PoPL 80/10/5/5 allocation applies only to fees actually collected and funded through its supported accounting path, replacing the earlier 50/30/10/10 candidate. It is distinct from Pons's creator/protocol split. No checked source establishes PoPL ownership of the creator payout or an automatic proportional share of hook revenue. On 2026-10-15, the user reported that the creator would send payments directly to a PoPL contract. Dedicated immutable per-bucket receivers accept and process those actual payments through the internal allocation. This user-reported intention is separate from the verified pool policy; no creator percentage or payment guarantee is assumed. See [creator-funded rewards](EXTERNAL_REWARDS.md).

The website's previous $425,000 / $1,250,000 = 34% liquidity example may illustrate TVL share, but it does not prove fee rights. Its assumed 0.30% fee and $864.96 daily PoPL revenue must not be presented as the real economics of this pool. Even for ordinary concentrated-liquidity pools, TVL share alone is not necessarily the active fee-earning share.

This research establishes pool identity and the read-time policy, not deployed PoPL compatibility, future revenue, or ownership of another protocol's fee recipients. Native LP settlement, hook behavior, creator-payment policy, and actual future pool/chain/provider integrations require review and validation before funded use.

## Pinned integration evidence

The [machine-readable inventory](../reports/production/current-pool.json) records block **88,544,093**, hash `0xc44dc8c95c6011b991312179f532935c2d94e4f21b84899d23896fd0fe01d490`, ten deployed code hashes, feed round and hook/factory policy reads. [Six actual fork tests](../test/UniswapV4Fork.t.sol) enforce the block identity and eight runtime hashes. Adapter mint, increase, swap, fee collection and position burn use an explicitly different hookless WETH/ZZZ pool initialized only on the local fork, with mock access and synthetic valuation feeds. They do not approve that pool or establish a production ZZZ price.

The actual ZZZ token's transfer and `burn(uint256)` reduce its local balance/supply by the expected amount on the fork. This does not validate bridged representations or total supply across future chains. The official [Chainlink Robinhood feed directory](https://reference-data-directory.vercel.app/feeds-robinhood-mainnet.json) provides ETH/USD proxy `0x78F3556b67E17Df817D51Ef5a990cDaF09E8d3A9`, eight decimals and 86,400-second heartbeat. The checked catalog has no ZZZ or sequencer feed; a safe ZZZ/USD source and chain-specific outage policy remain blockers. [Chainlink sequencer documentation](https://docs.chain.link/data-feeds/l2-sequencer-feeds) must be checked before selecting an actual feed.

The creator recipient can authorize a future recipient change through the Pons factory, and the factory owner has a delayed override. Those third-party authorities remain distinct from PoPL. The selected intake uses plain creator payments to a receiver rather than a Pons recipient change or automatic splitter. No live configuration, signed agreement or creator percentage is established by the repository.

[Provider lane observations](../reports/production/bridge-capabilities.json) distinguish messaging from asset support: direct Robinhood-to-Ink CCIP support was false while the checked LayerZero send library supported Ink and Ethereum. No backed ZZZ/WETH route, provider security configuration or exact atomic two-asset transport has been implemented or approved. Ordinary OFT dust/compose behavior requires additional design before it can satisfy `IZZZTransport`.
