# Actual market, price-source and low-fee route follow-up

20 November 2026. Baseline main `73658567cb605b58c992698e2103535e782269dd`.
**Production remains undeployed and NOT APPROVED.** No market, source, route,
financial guard, gas/fee/work limit or live configuration is changed.

## Result

The expanded read-only investigation does **not** establish a deployable market
configuration. It closes specific discovery and quote gaps in the previous
[market review](../market-feasibility-20261120/REVIEW.md): the other plausible
low-fee native pools, smaller reverse inputs, an independently documented pool
registry, and three newly identified WETH/ZZZ v3 markets.

The current selected native pool remains unusable for the tested ordinary
configuration. No tested alternative qualifies the complete contribution and
1% LP-reward conversion workflows. Independent valuation/publication also remains
open. These are actual-market and dependency decisions, not reasons to weaken
guards or replace the trusted F6 code speculatively.

## Actual observations

All observations bind chain4663, genesis and canonical block **119107223**,
`2026-11-20T14:07:35Z`. [Results](RESULTS.json) preserve the exact rational values;
these are dated observations, not configured live PoPL prices.

| Check | Result | Consequence |
| --- | --- | --- |
| Selected native pool `0x501122…afe1b` | Active L0. Full nominal-$50 ETH diagnostic loses14.263178% against its own starting spot; additional loss after known fees13.308707%. | Fails necessary ordinary execution screens. Active L0 does not prove every distant range empty. The diagnostic is not an assumed contribution swap fraction. |
| Largest known raw-active-L hookless pool `0x012aa4…3e551` | Same diagnostic loses1.382916% gross/0.286164% additional. Its ETH-per-ZZZ is5.811926 times the selected pool's. Tested1/100ZZZ reverse quotes report incomplete input. | A forward quote cannot establish two-way execution or compatible ordinary price bands. Raw L is not TVL, global rank or ownership/depth proof. |
| Previously untested native2999/6942-pip pools | Both directions tested;1/100/1000ZZZ and nominal-$5 ETH all return typed incomplete-input failures. | Low advertised fees do not make a route usable. Exact pool IDs and calldata remain in the evidence. |
| Native75-pip pool, combined95pips | All four normal-size diagnostics give an empty wrapped revert. A separate1M-gas1ZZZ diagnostic gives the same refusal. | Cause remains unknown. This is not proof of an out-of-gas or liquidity-only failure, and no operating allowance increases. |
| Fourth sub-1%-fee native key `0xb21d75…dc342` | Stored sqrt price falls outside the explicit finite diagnostic selection interval. | Recorded exclusion, not a newly invented admission rule. No quote or blanket all-route claim is made for this extreme-price market. |
| Stoa's documented current registry | Returns the native hooked `0x6538e2…391f` market, with core LP/protocol fee fields0. | Its hook is nonzero. Those fields do not prove zero effective swap cost or safe hook powers; current hookless PoPL readers/executors cannot admit it automatically. |

Nineteen native quote diagnostics produce2 positive outputs,12 typed
incomplete-input failures and5 opaque wrapped reverts. These are observations,
not19 passed financial operations. V4 positive output/gas lacks the complete
post-state proof required by LP3. The default3% contribution guard concerns
**actual marginal deployed LP**, including stronger caller/source/venue/idle
checks; an isolated swap-output screen cannot replace it.

## Broader market discovery: v3 is a lead, not an automatic fix

The [official Uniswap deployment registry](https://raw.githubusercontent.com/Uniswap/contracts/main/deployments/4663.md)
and [Stoa contract documentation](https://stoadex.com/docs/contracts) identify
the actual v2/v3 factories and WETH. Their read-only getters find no WETH/ZZZ v2
pair and three nonzero v3 pool addresses at the queried fees. Other cores,
forks, quote assets and unqueried fee tiers remain outside this finite search.

| v3 market | Address | Actual state/diagnostics |
| --- | --- | --- |
| 0.05% | `0x0d803c604c61598e9bf4dac4b22d6d75d9d08912` | Active L0; only609 raw WETH units and591 raw ZZZ units at the address. Five quotes refuse. |
| 0.3% | `0xfe290f54bd48afa72f3a463c65e61de558603a0b` | Active L0; approximately0.00000061713WETH and845 raw ZZZ units. Five quotes refuse. |
| 1% | `0xdd3c8aa6551bf5049310399c124cbb699b7d1c5c` | Positive active L; approximately0.973639WETH and3,690,115.654638ZZZ address balances. All five quotes produce output. Balances include any accrued/protocol/donated amounts and are not a principal-depth or TVL measurement. |

The1% market's nominal-$5/$50 WETH diagnostics lose1.048341%/1.481299% against
its own spot. Selling1/100/1000ZZZ loses approximately1.000039%/1.003859%/1.038578%.
All exceed the1% **gross** conversion screen against that starting price; all
pass the separate1% additional-loss-after-fees screen. These are distinct tests.
Its v3 protocol-fee share is not an extra fee added to the advertised swap fee.

The documented QuoterV2 address, runtime, `factory()`, `WETH9()`, token identities,
fees, spacing, balances, liquidity and slot0 are recorded. WETH decimals are read
as18. This is not independent recompilation or control approval of these new
dependencies. A positive [QuoterV2 exact-input result](https://raw.githubusercontent.com/Uniswap/v3-periphery/main/contracts/lens/QuoterV2.sol)
does not itself compare actual paid input with requested input at a global
price boundary; complete input consumption remains explicitly unproved here.

The current LP destination/move/reference/execution profiles accept native
ETH/fixed-ZZZ hookless v4. A WETH/v3 price or swap path needs separately reviewed
adapters, wrap/unwrap and callback/accounting boundaries, source/runtime pins,
gas and complete-operation qualification. No old WETH contribution input or
generic executor is restored. The newly found v3 market is not a ready PoPL route.

## Prices still need independent operating sources

Chainlink ETH/USD reads **$1,746.99672554**, age1,051seconds. Both checked proxies
still point to the same aggregator. Stored Pyth ETH remains$2,241.72518,
age1,158,502seconds, outside the existing hard one-day bound and3% agreement.
API3 `read()` still reverts; a current subscription/base/renewal cause is not
inferred from its revert. Operating max ages remain unapproved.

Pyth's [contract list](https://docs.pyth.network/pro/contract-addresses) distinguishes
stored Core prices from transaction-carried Pro verification. Its
[sponsored EVM list](https://docs.pyth.network/pro/sponsored-feeds) does not list
Robinhood. A deployed reader therefore does not establish fresh publication,
funding, monitoring and recovery. No update transaction, subscription, API key,
provider purchase or publisher installation occurred.

Two ETH feeds multiplied by one ZZZ market still share that ZZZ exposure.
Different pool addresses alone do not establish economically independent,
adequately funded price discovery. A possible ZZZ/USDG market or centralized
ZZZ/USDT order book is a future source-design lead, not a compatible on-chain
USD source. The chosen spot policy remains; no TWAP or API-price fallback is added.

## Concrete next decisions and acceptance

1. **Destination/depth:** retain the selected pool only with actual sustainable
   external liquidity and a market-consistent price, or deliberately select a
   different reviewed native-ETH/fixed-ZZZ hookless destination. This capture
   neither seeds liquidity nor selects a replacement. Tiny quotes or artificial
   qualification liquidity cannot establish launch viability.
2. **Conversion market:** obtain a compatible route with sufficient two-way depth
   at relevant sizes under the existing1% gross conversion limit. Preserve the
   separate known-fee/additional-loss and source/caller floors. None of these
   tested candidates is approved; raising the limit is not this task's solution.
3. **Valuation/publication:** identify genuinely independent fixed-ZZZ paths and
   a fresh independent ETH secondary, with exact implementations, controls,
   denomination, ages, publication/funding/renewal and outage procedures.
4. **Complete operation:** after those real inputs exist, simulate the exact
   current Entry/Vault/converter/maintenance workflow, actual marginal LP,
   post-withdrawal depth, full-input/post-state proof, original rights/reserves
   and complete fees under32M/full20% contributions and24M/full25% maintenance.
   Unknown review hashes/ages/depths/addresses remain blocked in the candidate.

These are separate P03/P04/P05 readiness obligations. A deployment listing,
highest raw L, positive quote or documentation cannot close them.

## Evidence, recorder correction and preservation

Six phases make117 read-only HTTP calls. Each keeps33 calls/90seconds maximum,
two-second start pacing,12-second absolute request deadline,256KiB responses and
no provider retries. Independent offline reconstruction verifies all raw
envelopes, code/data pins,95 native keys, calldata/fees, discovery getters,
canonical closures and exact rational diagnostics. See [verification](VERIFICATION.json)
and [evidence instructions](EVIDENCE.md).

The first16-call state phase stops on a recorder `KeyError`: the historical
aggregator runtime hash was nested under `runtime`. The original source and
failure remain. The corrected14-call continuation uses the same canonical
anchor and authenticated prefix, retrieves only missing fields and closes the
header again. It is not a provider retry, contract defect or silently successful
original phase. Exact old/current producer bytes are retained by hash.

No unit, Solidity, browser, compiler/static suite, populated local campaign or
unchanged provider test was rerun. The offline wire verifier is new evidence
verification, not independent protocol audit. Production code, F6 artifacts,
financial rights, all limits, original reports, four unrelated dirty tracked
files, existing Anvil/NFTs/LP/journals/checkpoints, sites/services, signer and
user-paused heartbeat stay unchanged. Zero transactions, deployment or sealing.
