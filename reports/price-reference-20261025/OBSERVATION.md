# Dated price reference: not a PoPL oracle policy

Observed **25 October 2026 at 00:02:43 Europe/Paris (UTC+02:00)** on Robinhood
mainnet, chain4663, block **97,093,373**:

`0x6bf28e0d8d5bad892230c20f037e8c1d8c04597ede73f97ebc078aaa135638b2`

| Reference | Observed USD value | Meaning |
| --- | ---: | --- |
| ETH/USD | $2,340.61 | Latest answer from the public Chainlink candidate; updated **24 October at 22:01:14 Paris**, not at the observation time. |
| ZZZ/USD | Approximately $0.01031019 | Selected ETH/ZZZ pool's instantaneous spot, multiplied by the ETH/USD answer. Not an independent ZZZ feed, execution quote or PoPL consensus. |
| Configured PoPL ETH/ZZZ output | Unavailable | Production source pairs are still unset and unqualified. |

These are historical observations, not live prices to copy into activation or
reporting code. [Saved values and provenance](reference-observation.json) retain
the full calculated ZZZ decimal, raw ETH answer/round, pool square-root price,
catalog entry and time. No configuration, transaction, approval or qualification
was performed.

## Sources and read boundary

- [Chainlink Robinhood catalog](https://reference-data-directory.vercel.app/feeds-robinhood-mainnet.json):
  ETH/USD proxy `0x78F3556b67E17Df817D51Ef5a990cDaF09E8d3A9`, eight decimals,
  catalog heartbeat86,400 seconds. No ZZZ-named feed was listed in that catalog
  at this read; this is not proof that no other/custom service exists.
- [Selected native ETH/ZZZ pool](https://app.uniswap.org/explore/pools/robinhood/0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b):
  native currency0 has18 decimals; ZZZ currency1
  `0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a` reports18 decimals.
- [Robinhood's public RPC](https://docs.robinhood.com/chain/connecting/): only
  `eth_chainId`, `eth_getBlockByNumber`, `eth_call` and `eth_getCode` were used.
  State reads used EIP-1898 canonical block-hash selectors and the block hash was
  checked again. StateView's runtime matched the existing reviewed venue pin.
  This does not qualify the RPC or all venue/token/provider dependencies.

For equal18-decimal currencies, the reference calculation is:

`ZZZ_USD = ETH_USD * 2^192 / sqrtPriceX96^2`

The catalog labels this ETH product **Shared SVR** and includes a secondary
proxy. Two proxies from one product are not two independent USD sources.
Product terms, common reporters/markets, proxy implementations/administrators,
update behavior, source precision, age and gas still require qualification.
The one-day catalog heartbeat is not an approved PoPL freshness setting.

## Read fees and operating costs

The current PoPL Oracle introduces no separate percentage, service-payment or
LINK transfer for a price read. Ordinary publicly accessible Chainlink push-feed
getters require no per-read LINK payment; on-chain reads within a transaction
consume network gas. Off-chain `eth_call` needs no chain transaction fee, but the
RPC provider may bill access. [Chainlink's interface](https://docs.chain.link/data-feeds/api-reference).

Do not generalize that to custom feeds, paid data/reporting products, VRF, hosting
or future provider agreements. Their costs remain unsettled. The Oracle's
500,000-gas ceiling is a maximum per external call, not a flat gas charge or a
measured full activation cost. Record actual gas, provider terms and who pays
before release. No exact production ETH/USD oracle cost was established here.

## Configuration and release status

After sealing, existing immediate governance can call
`setDualFeed(token,primary,secondary,maxDeviationBps,reviewHash)` to replace either
or both sources with a newly admitted immutable policy record. Review both
sources and update the approved inventory/API/keeper profiles; no redeployment
or added timelock is required for compatible sources. The retired `setFeed`
reverts. Fixed Oracle code, source-call bounds and lifecycle controls remain.

Selected disagreement tolerance remains3%, separate from the default1% execution
floor; no averaging, spot fallback or automatic cap increase. [Price security](../../docs/PRICE_SECURITY.md)
and the [single Todo](../../TODO.md#task-dual-price-qualification) remain authoritative.
This documentation update reuses the unchanged source-bound verification; no
Solidity/website tests were rerun. Production remains **NOT APPROVED**.
