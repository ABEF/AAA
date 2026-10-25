# Feed and route qualification progress - 25 October 2026

This pass implements an optional hardened Pyth Core reader and advances the
actual source shortlist. It does not qualify or deploy a production price pair,
route or RPC. [Operator procedure](../../../docs/PYTH_PRICE_SOURCE.md) and
[verification](VERIFICATION.md) keep code capability and external approval distinct.

## Concrete source candidates

The official [Chainlink catalog](https://reference-data-directory.vercel.app/feeds-robinhood-mainnet.json)
and [Pyth symbol API](https://pyth.dourolabs.app/v1/symbols) were downloaded at
02:02:09 UTC / 03:02:09 Europe/Paris on 25 October 2026. The local download wall
time in `catalog-receipt.json` is the authority; catalog rows are not on-chain
observations. The clock change occurred that night; use the explicit UTC time
rather than assuming a fixed Paris offset for a whole date.

| Asset | Chainlink candidate | Pyth Core/Hermes candidate ID |
| --- | --- | --- |
| ETH/USD | `0x78F3556b67E17Df817D51Ef5a990cDaF09E8d3A9` | `0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace` |
| USDG/USD | `0x61B7e5650328764B076A108EFF5fa7282a1B9aD2` | `0xdaa58c6a3ce7d4b9c46c32a6e646012c17c4a2b24c08dd8c5e476118b855a7da` |
| USDC/USD | `0x9e6f4605992a899ee2999999f3ec80c41f452546` | `0xeaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a` |

The [official Pyth address list](https://docs.pyth.network/pro/contract-addresses)
lists Robinhood Core `0x8250f4aF4B972684F7b336503E2D6dFeDeB1487a`
and Pro `0xACeA761c27A909d4D3895128EBe6370FDE2dF481`. They use different
interfaces and IDs. The selected catalog spot rows have exponent -8 and minimum
publisher count 3. That count and a provider label do not establish independent
markets, safe administrators, correct deployed code or sustainable updates.

Pyth Core and Pro share one backend; Chainlink Shared-SVR primary/secondary proxies
also do not form two independent providers. A reviewed Chainlink-plus-Pyth pair
is a useful candidate direction for ETH and the two stablecoins, subject to
publisher/market/common-mode, proxy and product review. No production selection,
maximum age, confidence setting or independence ID is inferred.

No ZZZ-named product was found in either downloaded catalog. This bounded
catalog result does not prove every custom feed is unavailable. Ask the ZZZ team
and candidate providers for an exact asset-specific source and its independent
market/history/manipulation/administration review. The LP itself contains ZZZ,
so accepting ETH instead cannot bypass that requirement.

## Implemented reader and reviewed limits

The new [immutable reader](../../../src/ZZZPythPriceFeed.sol) supplies the exact
Oracle methods while preserving the Core timestamp and precision. Its review,
runtime, feed ID, exponent, maximum age and confidence policy are immutable.
Exact bounded calls and ABI validation reject stale/future/nonpositive/oversized/
malformed/reverting observations. It has no owner, price setter, update function,
payment, fallback, custody or arbitrary execution surface. Existing Vault/Oracle
source is unchanged. The new reader is optional and absent from production config.

The [maintained SDK's AggregatorV3 adapter](https://github.com/pyth-network/pyth-crosschain/blob/main/target_chains/ethereum/sdk/solidity/PythAggregatorV3.sol)
was considered. Its payable update/refund surface and dynamic exponent handling
do not enforce this project's fixed confidence/runtime/bounded-response policy.
This narrower reader implements only PoPL's two current methods and does not
pretend to provide historical round data. Its runtime pin does not pin a Core
proxy implementation or eliminate accepted upstream governance trust.

Pyth's [current sponsored list](https://docs.pyth.network/pro/sponsored-feeds)
does not list Robinhood. [Core update documentation](https://docs.pyth.network/pro/use-prices-on-blockchain/evm)
requires signed updates and an update fee where needed; the
[post-August upgrade guidance](https://docs.pyth.network/pro/pyth-core-upgrade)
requires authenticated Hermes access. Update service, operating budget, data
plan, source control and failure recovery stay open. No API key was requested,
read, created or placed in reports.

## Actual public read attempt and route status

The sandbox transport initially could not reach the catalogs. Explicitly approved
external read access succeeded; selected records plus full-download digests are
saved. Full raw catalogs remain in the external release workspace, avoiding a
5-MB data dump in Git. The selected records are evidence extracts, not an approval.

Fresh bounded Pinax chain reads returned HTTP429 on the first attempt and on one
delayed retry. Robinhood's documented public RPC returned HTTP403. Neither got
as far as a usable canonical feed/route snapshot. These are environment/provider
availability observations, not zero prices, missing pools or qualification passes.

The report-local discovery driver prepares an explicit same-hash check of the
reviewed v3 factory/Quoter and standard 500/3000-pip ZZZ/WETH, ZZZ/USDG, USDG/WETH
and USDC/WETH pool identities. Route discovery was **not executed after the
provider failures**, and no new quote is claimed. It is discovery groundwork,
not a live pricing or transaction path. V4 alternative initialization discovery
is outside this bounded search; no absence of all cheaper pools is inferred.

The selected hookless principal pool still has its historical approximately1.101%
combined fee, which exceeds the retained1% full-reward conversion budget at a
neutral reference price. A currently funded, independently priced cheaper route
must be quoted and exercised in the complete reviewed conversion. A nominally
cheaper fee, a single-block factory address, a third-party screener or a partial
USDG route cannot close the native ETH payout gate. No cap is increased.

## Remaining decisions and exact next inputs

- Obtain two independently reviewable ZZZ/USD source proposals with real market
  coverage, exact correct-chain integration, age/deviation, control and cost terms.
- Review the Chainlink/Pyth candidate pairs and fund a target-chain update service;
  obtain reliable archive/trace-capable RPC credentials or endpoints separately.
- Supply an initialized, liquid cheap ZZZ-to-native-ETH route, or a reviewed v3
  WETH route with its explicit wrapper boundary. Demonstrate the1% conversion floor
  at realistic batch sizes and the2% complete contribution floor, with gas separate.
- Record actual source runtime/proxy/administrator pins, admitted policy IDs,
  real signed-update/proof checks, quote round fingerprints and operating outages.
- Independently review the adapter and whole protocol; these local tests are
  implementation evidence, not an independent audit or production approval.

No public transaction, deployment, service/restart, signing policy, website,
existing Anvil/NFT/LP/balance/journal or paused-monitor state changed.
