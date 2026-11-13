# Fresh market and feed qualification — 13 November 2026

**No usable production feed/route configuration is qualified.** The new evidence identifies concrete market changes and launch actions without changing safeguards, configuration or the selected LP pool. Source baseline: `11e74883787e32e816b5c01b1213189400fe01fe`.

All state observations bind Robinhood4663 block **113296579**, hash `0x3b7d5a7153c2e60e8b2beadd3e46b4e1e5859a1611f54585abd3c222b9423e31`, **10:48:31UTC**. The original phase stopped on HTTP429; a separate, approved phase after other serialized work/cooldown completed the missing StateView liquidity cross-check, four bounded quote diagnostics, and numbered-header checks before/after. The original partial capture and denial remain immutable. No missing denial headers are invented.

## What changed

The selected hookless native ETH/fixed-ZZZ pool `501122…` now has **zero active liquidity**, corroborated by core storage and StateView. It previously had nonzero active liquidity on9November. This does **not** mean all its ticks are empty: a fresh ETH quote successfully crosses into executable liquidity. Initial activation could create a new main position, but still needs compatible independent pricing, external swap depth and the actual marginal-LP checks. No reseeding/fallback is enabled.

The bounded historical inventory contains95 hookless static native pools; eight states changed. Seven currently have active liquidity and pass the strict principal **fee-only** admission filter. This is not a fresh initialization-log scan, global-highest-TVL claim, ownership proof, usable bidirectional depth or admission approval. Runtime pins for core/StateView/quoter/ZZZ match the prior independently recorded bindings before storage-layout interpretation.

| Current candidate, ordered by activeL | LP fee, pips | ZZZ-per-ETH price / selected price | Possible common reference at500bps ceiling |
| --- | ---: | ---: | --- |
| `012aa49a…` |10009|0.172060|No|
| `19820dbe…` |10023|0.559915|No|
| `9fa18577…` |10018|1.495060|No|
| `6db792e1…` |96500|1.444799|No|
| `7e78b246…` |49000|1.468110|No|
| `1e2ed408…` |20000|1.499665|No|
| `07ee2b09…` |10015|0.948233|Yes, necessary geometry only|

The continuous-price band-intersection test is `max(P)/min(P) <=105/95`, with `P=sqrtPriceX96²/2¹⁹²`; Solidity's fixed-point roundoff does not bridge these material gaps. The500bps Registry ceiling bounds the physical **price** ratio, not the square-root ratio. Larger-activeL candidates therefore cannot simply replace the reference/route while keeping the selected destination under current guards. The one geometrically compatible active candidate is extremely small. Current activeL ranking is neither TVL nor remaining depth after a future PoPL withdrawal. The selected destination is unchanged.

## Fresh feeds

| Candidate | Exact observation at anchor | Decision |
| --- | --- | --- |
| Chainlink ETH/USD proxies `78f355…` / `5058ad…` |$1952.06966758; age2235seconds; same aggregator `6091e6…`|One candidate service, not two independent feeds. Source maxAge/liveness/control acceptance remains unapproved.|
| Pyth Core ETH/USD `8250f4…` |Stored$2241.72518; age541758seconds;1483.837986bps above Chainlink|Stale beyond hard86400seconds and outside300bps agreement. No valid second observation.|
| API3 ETH/USD proxy `3c57b1…` |`read()` / `latestRoundData()` revert; ETH name/subscription/base remain zero|Inactive observed candidate. Activation and round-compatible adaptation require separate review if selected.|

The tested API3 ZZZ/USD name/subscription are also zero; this is not proof that no custom source exists. No two genuinely independent ZZZ/USD paths have been qualified. Two readers of one ZZZ pool multiplied by different ETH feeds repeat the same manipulable ZZZ exposure.

Pyth's zero stored update-fee values do not make stale prices current. Its current official docs describe pull updates and freshness checks, and API3 documents that its proxy lacks Chainlink round semantics; our Oracle requires positive, coherent rounds. Any required adapter, authenticated data publication, funding and outage recovery remains an explicit release task. No update, subscription, adapter deployment or payment occurred. See [primary references](PRIMARY_SOURCES.json).

## Four new200k quote diagnostics

The ETH input is **0.025613839931228220ETH**, sized as nominal$50 from the single observed Chainlink round. This is a conditional half-of-$100 input diagnostic, **not** the strategy's proved optimal swap fraction or a qualified activation. The reverse input is exactly1000ZZZ, without an approved USD label.

| Venue and direction | Actual official response | Interpretation |
| --- | --- | --- |
| Selected ETH→ZZZ |6257.066880691536778018ZZZ; quoter-reported98520gas|14.211291% loss against that venue's own initial spot.|
| Selected1000ZZZ→ETH |Canonical wrapped `NotEnoughLiquidity(selectedId)`|Exact full input incomplete. No partial fill is reported as success.|
| `07ee2b…` ETH→ZZZ |1061.276548164277345379ZZZ; quoter-reported97694gas|84.654786% loss against its own initial spot.|
| `07ee2b…`1000ZZZ→ETH |Canonical wrapped empty revert bytes|Unavailable at200k; do not infer a precise liquidity/gas failure.|

Both positive ETH quotes strongly fail analytical3% total/1% additional floors at their own initial spots. `RESULTS.json` retains exact fractions, known directional fees and the diagnostic assumptions; these are not production two-source floor simulations. Official full-input semantics are authenticated against the unchanged pinned quoter and dependency sources. Its ABI returns output and gas, **not post-swap spot**. No postspot, exact current tick replay, whole activation/growth acceptance, conversion acceptance or full operation gas is fabricated.

## Concrete launch actions

1. **Operator/provider:** qualify a second independent ETH service, publication reliability, reviewed maxAge, round compatibility and network-liveness policy. Pyth needs fresh authenticated updates; API3 needs activation and a reviewed compatible adapter if selected.
2. **ZZZ creator/operator:** supply two genuinely independent ZZZ valuation paths and meaningful external bidirectional depth. Resolve the large price incompatibility between the selected pool and larger-activeL candidates. Changing the destination requires a separate explicit decision.
3. **Operator:** once those inputs exist, approve actual source/route policies, immutable reader pins, liquidity floors and genuine review fingerprints. [CANDIDATE_CONFIG.json](CANDIDATE_CONFIG.json) is deliberately incomplete and nondeployable; no source independence or age/depth policy is guessed.
4. Qualify actual$100 activation/$5 growth, whole earned conversion, post-withdrawal maintenance depth, gas/fees and operations with that real graph. Existing controlled/synthetic gas evidence remains separately scoped.

## Verification and limits

**58 read-only attempts:53 valid results,4 explicit RPC errors,1 retainedHTTP429.** The original51-read phase has48 results/two API3 errors/one denial; the seven-read closure adds five results/two quote errors. Closure calls use2-second spacing,12-second timeout and256KiB response bound; no refusal or transport retry occurred. There were no public transactions, keys, signing, chain overrides, EVM test reruns, unchanged suites, compiles, service/site/local-chain changes or automatic provider adoption.

[verify.py](verify.py) checks public byte hashes,57 exact response bodies, chain/anchor selectors, runtime hashes, PoolKey identities, bulk storage words, current state/round calculations, exact quote inputs/output math and denial/error boundaries offline. [RESULTS.json](RESULTS.json), [SOURCE_BINDINGS.json](SOURCE_BINDINGS.json), compressed original/closure captures and [RAW_INDEX.json](RAW_INDEX.json) retain provenance. Historical9November696 quote calls are referenced at their original scope, not rerun or relabeled. Preservation of ETH/fixedZZZ, spot choice, two-source300bps agreement, contribution3%/97% deployed, conversion1%, maintenance3%, additional1%, caller limits and all other safeguards is explicit.
