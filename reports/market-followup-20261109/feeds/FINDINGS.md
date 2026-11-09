# Actual oracle follow-up

Release admission remains **blocked**. Read-only evidence adds an actual API3 ETH
candidate and concrete controls/costs, without changing source, policies,
configuration, on-chain state or services. The canonical shared anchor is chain4663,
block110324511, hash`0x49759bb8363ba4e95b5b090fd7bee113949b100ab1fa408a839603dc31f4e6b9`,
9November2026 20:04:50UTC. [Decoded evidence](FEED_FINDINGS.json) retains exact
raw calls, runtime pins, authorities, source references and failures.

## Current ETH sources

- Chainlink proxy`0x78F3556b67E17Df817D51Ef5a990cDaF09E8d3A9` returned
  $2125.61,8decimals, round18446744073709554844, updated20:02:37UTC,
  age133s. Secondary`0x5058aDee53b04e374d8bEDbAD634Bc4778F50b22` still
  uses the exact same aggregator`0x6091e64eb7138eef066a80fd3a0d7427b91f2721`.
  The catalog has86400s heartbeat/0.5% deviation; no operating maxAge was selected.
  Owner`0xee27d5ae494300902d90454e8630a3f1c68c9c52` returns4of9 owner/threshold
  getters. Exact-source getter`getTransmitters()` returns10addresses. The mapped
  ConfigSet event authenticates the matching digest/count,10signers,10transmitters
  and f=3; all transmitters reconcile with the shared-anchor getter. Its
  `block.number` is ancestor-chain height25245315, mapped to RPC L2event33090.
  An initial empty unmapped-block lookup is not absence evidence. Old failed
  `transmitters()` calls are preserved as ABI lookup failures, not zero reporters.
  The explorer source is partially verified and its reported deployed bytes match
  the observed23186-byte runtime; there was no independent recompilation. Current
  operator identities, underlying markets, off-chain configuration meaning and owner
  modules/guards remain unqualified. Standard reads have no per-read LINK payment;
  these calls do not qualify actual gas/provider cost or ongoing feed funding.

- Pyth Core`0x8250f4aF4B972684F7b336503E2D6dFeDeB1487a`, exact ETH
  ID`0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace`,
  still stores $2241.72518 from7November04:19:13UTC: age229537s exceeds the
  hard86400s maximum. Confidence is8.809376bps; that does not repair age.
  Exact agreement check`(high-low)*10000 <= low*300` fails at546.2675655bps.
  Implementation`0x66e9cba5529824a03b5bc9931d9c63637101d0f7` is unchanged;
  governance emitter and verifier`0xb27e5ca259702f209a29225d0eddc131039c9933`
  are recorded, including five current verification keys. Actual quorum getter
  reverts; documented3of5 is not independently established solely by counting keys.
  Live single-update and transaction-fee getters both return0, consistent with
  [current Pyth fees](https://docs.pyth.network/pro/on-chain-fees). This is more
  than an empty-array fee query, but no signed packet, funded update operation,
  network gas or recovery was qualified. The unauthenticated current Hermes request
  returns401. [API authentication and ongoing plans](https://docs.pyth.network/pro/pyth-core-upgrade)
  remain separate from on-chain fees. Stored freshness is not off-chain packet availability.

## New API3 candidate

The official Robinhood deployment and public app catalog identify ETH/USD.
Its actual communal proxy`0x3c57b17052bdd5ff75b1f03c5f3afddbcfb8de1c`
exists, has18decimals/dAppID1 and implementation
`0x618934db51db175054be0ba587296ab1a7733afc`. Its name binding,
subscription and update parameters are unset; its reads revert. The catalog's
actual base feed`0x5494cb529af981f0d6484ca21d839f27bf2948c8f5599ac8dd9809966caef9bb`
also has timestamp0 and empty registry details at this anchor. This is an
uninitialized observation, **not a zero dollar price**.

The literal base-feed mapping is authenticated beyond its display label: all292
management leaves recompute the app's exact Merkle root, which matches API3Market's
on-chain management root at the separately labeled fresh anchor110332661,
`0xe209c7bbac02c6f4ce5b397bc8dda0f8618ce24dca8818c43163faaf1151514f`,
20:18:44UTC/depth13. That fresh snapshot again returns base timestamp0/empty
details, the same Chainlink round(age967s), and the same Pyth observation
(age230371s). It never replaces the original shared market/price anchor.

Five90-day ETH offer proofs independently verify against the exact pricing root
read from API3Market at the anchor. All have86400s heartbeat, with deviation
thresholds5%,2.5%,1%,0.5%,0.25% and published price parameters respectively
0.014797515243100114,0.026371145363189660,0.083904245318021024,
0.259767021838641312,0.941077986370735360ETH. These are product-offer parameters,
not selected PoPL policies or final funding quotes. Actual payment also depends
on sponsor-wallet balance/readiness, queued subscriptions and network gas.
No subscription was purchased or payable call simulated.

API3's [actual source](https://github.com/api3dao/contracts/blob/bd8b08d7aa2203c5f3f103d4600b3b9f39d30e1c/contracts/api3-server-v1/proxies/Api3ReaderProxyV1.sol)
sets both round IDs to0. Current PoPL correctly rejects that interface even after
activation. A separately reviewed immutable reader preserving original timestamps
and enforcing exact fields, upstream runtime/control pins and funded liveness
would be new work; no guard was relaxed or adapter implemented here.

Proxy/factory/market control goes through forwarder
`0x0F52eE9C03cb939F25286D05A846208642f45A32` to
`0xbAC8d514d284df81Fc21DE80925d2e0721bF06B5`, with4of8 getters.
There is no literal overlap between the captured API3 and Chainlink admin-owner
sets or the Pyth verification keys. This does not establish independent people,
organizations, markets, infrastructure, Safe modules or delegates. API3's catalog
provider labels are not an activated ETH reporter set.

## Fixed ZZZ and liveness

Fresh Chainlink62-row and Pyth3946-symbol catalogs, plus API3's292-row app catalog,
provide no fixedZZZ match. API3's ZZZ/USD offer returns404, on-chain name is unset
and computed proxy has no code. Custom/private services remain unresolved.
Exact-token LBank/XT books in the [parallel evidence](../review/cex-findings.json)
are genuine external-market leads, but are not existing authenticated on-chain USD
feeds or proof of independent reporters. USDT/USD, publisher controls, depth,
update service, ABI and outage behavior remain qualification work.

[Chainlink's uptime list](https://docs.chain.link/data-feeds/l2-sequencer-feeds)
does not list Robinhood and says it is no longer expanding to additional networks.
No address or always-up substitute was invented. Source/provider and chain-outage
policies remain open.

The official public RPC served the initial canonical state reads but by20:16:17UTC
retained the header while refusing its historical state. A bounded public Pinax
retry verified the same chain/header/hash and returned the API3 base data above.
Successful individual reads do not establish archive retention or operating availability.
