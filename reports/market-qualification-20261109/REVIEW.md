# Actual ETH/ZZZ feeds and execution qualification

Baseline main `99a01e97887156be0d31b61d453df4e29eb8a055`,9 November2026.
**Production NOT APPROVED.** Public calls were read-only. Actual transaction
execution occurred only on a new disposable fork, now stopped. Existing8902,
NFTs/LP/balances, sites, services, journals, signer and paused heartbeat are unchanged.

## Result

The campaign establishes concrete reasons the current release cannot yet be
qualified against these dependencies. It does not establish a usable independent
USD source pair, a default1%-eligible ZZZ-to-ETH conversion route, or successful
activation/growth at the recorded unmodified market and rehearsal settings.
No financial limit or production configuration was changed to obtain a pass.

It also corrects an overly broad interpretation of the earlier “thin depth”
result: an activation rejection alone does not prove a solver bug or globally
insufficient liquidity. The actual trace must identify which price, output,
placement or execution guard binds. Here the selected pool has direction-specific
capacity and the rehearsal's own configured guards limit the ETH balancing trade.

| Area | Actual finding | Required next work |
| --- | --- | --- |
| Independent ETH/USD | Chainlink reference readable; both listed proxies use the same aggregator. Observed Pyth ETH is stale and disagrees beyond3%. | Qualify fresh independent updates or another source, costs and upstream controls. |
| Independent fixedZZZ/USD | No match in the retrieved Chainlink/Pyth/RedStone catalogs. | Obtain and review two actual independent sources for this exact token; private/custom products remain unresolved. |
| ZZZ-to-ETH conversion | No tested quote establishes default1% eligibility. Selected pool cannot fill meaningful reverse input at this anchor. | Review genuinely executable depth/price and all converter floors; preserve backed source-currency rights meanwhile. |
| $100 activation | Both asset cases atomically revert in the controlled-price, unmodified-market fork. | Qualify real price pairs, reviewed operating settings and full execution together. |
| $5 growth | Blocked because neither initial activation succeeds. | A genuine active NFT is prerequisite; no synthetic incumbent was inserted to manufacture this result. |

## 1. Actual price-source observations

The [pricing record](pricing/pricing-findings.json) retains original official
catalogs, rounds, proxy/implementation/owner observations, HTTP failures and
source hashes. Its canonical block is109785732,
`0x4f11bc04863fc640f16c8b8392924b17fe118cb7735416c57cdfa4cda9d9ce92`,
9November04:39:04UTC /05:39:04Paris. These are dated references, **not configured
PoPL prices or values to copy into an operating inventory**.

| Candidate | Observed reference | Constraint |
| --- | --- | --- |
| Chainlink ETH/USD `0x78F3556b67E17Df817D51Ef5a990cDaF09E8d3A9` | $2142.10382193; updated03:06:50UTC, age5534s | Eight decimals, actual round captured. Its secondary proxy shares the exact same aggregator and owner; not independent coverage. Actual chosen maxAge/authority/source review remains open. |
| Pyth Core ETH `0x8250f4aF4B972684F7b336503E2D6dFeDeB1487a` | $2241.72518; published7November04:19:13UTC, age173991s | Exceeds the Oracle's hard86400s age bound. Pair spread465.063bps also exceeds300bps. A compatible reader does not fund or update the Core. |
| Fixed ZZZ `0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a` | No matching source in retrieved catalogs | Chainlink62 rows, Pyth3945 symbols, RedStone798 push deployment rows/1760 pull-map entries. Absence there is not proof that no custom/private service exists. |

Two wrappers around one aggregator, different round IDs or invented independence
IDs cannot satisfy the requirement. A ZZZ value derived from the selected pool
and one ETH feed is useful for explicitly conditional diagnostics; it is not an
independent ZZZ feed. Disabling ZZZ as a contribution input would not by itself
remove the LP's need to value ZZZ.

Pyth needs a qualified authenticated update service and funding or an actual
alternative; no sponsored Robinhood updater was established. RedStone pull data
cannot simply be substituted into the existing static source ABI. Both sources'
underlying markets/reporters, proxy and governance controls need review. The
Pyth proxy implementation was observed at the same anchor; zero EIP1967 admin or
owner slots do not prove immutability because the Core retains a governance source.

No correct-chain Chainlink uptime-feed address was identified in the retrieved
official supported list. A generic Robinhood uptime-check example is not a
deployment address. This needs an explicitly reviewed chain-liveness policy,
not an Arbitrum address, fabricated always-up response or silent fallback.
The research RPC hit429 and an explorer source API hit403; successful research
reads are not production availability, source-control or archive qualification.

## 2. Bounded actual-market discovery

[Market findings](markets/MARKET_FINDINGS.json) bind block109785803,
`0x4a55b88b470e9dd41d7bf885c80f33a0886d66444cf1ba4223ff2128c9da9498`,
9November04:39:10UTC /05:39:10Paris, with canonical rechecks. The exact same-anchor
ETH round and selected sqrt price were captured. Derived ZZZ reference is
approximately$0.00752271384553421; it is **selected-pool spot times one ETH feed**.

The investigation captures102 native ETH/fixedZZZ v4 Initialize keys,71 hookless
fee-compatible states,3 v3 factory candidates and107 size/direction quote calls.
Discovery is bounded and provider-dependent, not a global best-route promise.
Official deployment registry commit is
`12e3736496b10bcaa3aecb6c787d4a6c57a2c76d`. Actual code, ABI, core/factory bindings,
verified sources/licenses and original failed calls are retained. Source/runtime
matching is not an independent recompilation or contract audit.

The selected pool remains native ETH/fixedZZZ, static10020pips, spacing200,
hookzero; observed protocol fee1000pips per direction gives combined11010pips
(1.101%). Another swap venue is distinct from the NFT's principal LP destination.
Principal balancing admits reviewed native-v4 venues only; a v3/WETH pair is
an optional earned-conversion venue, not a principal/contribution venue.

### Active liquidity is not bidirectional depth

Selected sqrt is42277818571609234285824917886142, stored tick125599 and active
L962337799357516411500. At125600, liquidityNet is exactly the negative of that
active L; upward crossing removes it all. No higher initialized tick appears in
the captured current bitmap word. Integer TickMath shows only384278 net raw ZZZ
to that next boundary and approximately1wei ETH output before crossing.

Actual-core tracing independently confirms a1ZZZ request consumes only388557
raw ZZZ and returns1wei ETH before the current callback rejects incomplete input.
A1raw-unit request consumes that unit but returns0ETH and is also rejected.
The official quoter's decoded `NotEnoughLiquidity(poolId)` means requested input
was not completely consumed; it is not treated as an arbitrary generic RPC error.
These facts explain the measured direction/size failures at this anchor; they
do not prove that future liquidity or every external route must fail.

### Price and size matter as well as fee

The following are **swap quotes**, not completed activations. Inputs use the
single-feed reference for sizing, not qualified USD consensus.

| Native input | Selected10020 output ZZZ | Own-spot loss | Alternative10018 output ZZZ | Own-spot loss |
| --- | ---: | ---: | ---: | ---: |
| 0.023341539045923007ETH (about$50) | 6490.280350783546197553 | 2.350956% | 6854.847537441526775516 | 9.049409% |
| 0.001167076952296150ETH (about$2.50) | 328.457737121947437697 | 1.164257% | 371.074779454490326905 | 1.531084% |

Alternative pool `0x9fa18577c6a55769bab7ee3e3885b3a1b32ef6f8e898386638b1147b3c8d7155`
has fee10018/spacing200/hookzero. Its ZZZ-in-ETH spot is11.81328% below selected
spot (the reciprocal ZZZ-per-ETH ratio is13.396% higher). Better token output
against the selected spot therefore does not prove lower impact, an independent
price or admissible execution. No reference/spot rule was loosened to approve it.

V3 ZZZ/WETH0.05% and0.3% candidates fail the tested fills. The liquid1% candidate
quotes1000ZZZ to0.003029292353745119ETH-equivalent WETH:1.0353% below its own spot,
and approximately13.7405% below selected spot. Neither comparison supplies
independent USD truth; neither establishes a1%-eligible conversion.

V3 capability additionally needs a reviewed nonzero immutable wrapper selected
before converter binding/sealing, actual wrapper/route policies and ETH/ZZZ/WETH
pricing. The observed WETH is an upgradeable proxy; controls need review.
Wrapperzero cannot later become nonzero. Fresh7 automated conversion remains
native-v4-only even though existing contracts have a separate v3 capability.
No worker/profile, constructor choice or operating inventory was changed here.

## 3. Full actual-market activation diagnostics

The [fork record](fork/EVIDENCE.md) reuses all90 exact current normal production
source objects. No production compile or unchanged Solidity suite was repeated.
It predeploys the renderer for the three-argument NFT constructor. The local
LP-only fixture explicitly leaves SeaDrop unbound and directly mints two dormant
NFTs; this is **not** primary mint2/OpenSea release admission. Four controlled,
correlated price observations use the captured ETH/selected-pool vector. They
are not independent feeds. No synthetic market depth or incumbent LP was inserted.

The deployment's pool/reference deviation is100bps and per-swap slippage200bps,
with additional-loss100bps, aggregate contribution200bps and idle500bps.
These are recorded **rehearsal settings**, not selected production policies:
production inventory spot/slippage fields remain null. The separate3% source
agreement allowance cannot be substituted for any of these execution settings.

| Case | Actual result |
| --- | --- |
| ETH100USD activation | Local transaction reverted. All eight candidate quotes succeeded within approximately72–74k gas, below200k; no quote-gas or iteration-budget bug is established. |
| ZZZ100USD activation | Local transaction reverted; quote calls reject incomplete reverse fills. |
| ETH/ZZZ5USD growth | Blocked because no genuine activation succeeded; these are not successful growth cases or tested-growth acceptance. |

For ETH, the initial0.018365377021269272ETH quote returns
5120.419880394585201968ZZZ. It is below the gross2% swap floor
5124.976732321734567559 but above the fee-net/additional1% floor
5120.270643993758632877. Its1.98428668% post-swap spot deviation also exceeds
the configured1%. The selected smaller trade0.009182688510634636ETH returns
2573.038008076697321139ZZZ and meets those swap/spot bounds, but leaves too much
undeployed value. Rolled-back internal values are:

- Would-be new LP:50.882607835024253894USD.
- Would-be idle:48.803348659196923858USD.
- Retained total:99.685956494221177752USD.
- Permitted5% idle at that checkpoint:4.984297824711058887USD.

`assertDeployed` correctly rejects this before the98USD marginal-LP test can
complete. Retaining value in idle does not satisfy the user's actually deployed
LP requirement. These trace values are **not post-transaction user balances or
losses**: the operation rolls back, NFT/LP/Entry state and input balances return,
and only local network gas is paid. Exact token approval is separate and remains
subject to its normal allowance semantics. Failed receipts carry no successful
LP/activation logs. No image, share or portfolio update is justified by them.

The result establishes an interaction between actual state and configured
per-swap, spot and idle guards. It does not authorize removing guards, increasing
the contribution2% or conversion1% caps, recommending a production setting, or
claiming every possible reviewed route is infeasible. Future real prices,
liquidity and settings need a new exact full-operation review.

## 4. Improvements and remaining decisions

This campaign makes qualification reproducible and guard-specific instead of
equating existence, TVL, active L, a cheap fee, a swap quote or retained value
with usable LP deployment. It corrects current guides that still described a
royalty converter, old accounting/canonical identities and an obsolete static
default. The operator procedure now distinguishes all price/route/immutable
wrapper/worker boundaries. Todo evidence and memory are updated; statuses remain
open rather than marking failed or blocked cases complete.

No production Solidity/backend defect requiring a code change was demonstrated.
Existing atomic and full-input checks prevented the observed failures from
becoming incomplete user operations. No financial policy was silently selected.

Before approval, obtain two defensible fixedZZZ sources with the team, a working
independent ETH update/provider arrangement, reviewed sequencer/upstream policy,
real executable route/depth and explicit operating settings. Then measure actual
full activation/growth/conversion, target gas, provider and recovery behavior,
matching consumers and independent audit. The [sole Todo](../../TODO.md) owns
these requirements; [verification](VERIFICATION.md) records what ran and did not.
