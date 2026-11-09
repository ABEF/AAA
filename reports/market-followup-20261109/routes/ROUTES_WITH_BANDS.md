# Actual route follow-up — 9 November 2026

Read-only public-chain evidence; production is not approved. No contracts, policies, running systems or local chains changed.

Anchor: block **110324511**, hash `0x49759bb8363ba4e95b5b090fd7bee113949b100ab1fa408a839603dc31f4e6b9`, **20:04:50 UTC**, canonical rechecked. Baseline `509d4fd7f2e42cdd278f913f7863e37cfd006d6d`.

The refreshed bounded search finds no new initialized direct native-v4 or v3/WETH pool since block109785803. Four earlier pool states changed; selected pool did not. Complete v3 enabled-fee logs establish100/500/3000/10000pips, with only500/3000/10000 producing fixedZZZ/WETH pools. The95 hookless static v4 states include24 conversion-only fee tiers above the principal10% fee ceiling, six of them active but previously unmeasured. These six are not described as newly funded.

All15 empty-active-L low-fee venues were tested in both directions at14 vectors, rather than assuming zeroL meant no executable ticks. None returned a quote. Another already-known4%-fee empty-active-L venue667a9f… does cross a gap for a tiny ETH input (1,000,000wei ->183,059,909,303rawZZZ); its11 added operation/fee vectors all reject incomplete input. This is not a cheaper qualifying route.

The initial size/capacity capture contains **673 official quote calls**:646 main(175 responses/471 errors),11 gap follow-ups(all errors),16 exact capacity probes(13 responses/3 errors). Raw failed calls are retained. Nine core/token/router/quoter runtime hashes match the earlier evidence.

Selected reverse capacity is exceptionally small: **388,557 raw ZZZ (0.000000000000388557 ZZZ) ->1wei ETH** consumes input fully and removes currentL at upper tick125600;388,558raw fails the official full-input quote. A1raw probe returns0ETH and cannot satisfy positive output. Larger reverse requests remain actual failures, not successful partial fills. Captured tick math does not assert that unobserved distant words have no liquidity.

The following selected ETH-to-ZZZ quotes use a single ETH/USD round ($2125.61) and selected-pool-derived ZZZ size vector. They are conditional diagnostics, not qualified USD valuation or completed contributions. Own-spot loss includes fees; postspot is calculated by exact integer swap replay, matching official outputs.

| Size label | ETH input | ZZZ output | Own-spot loss | Postspot deviation | Prior2% swap floor | Prior1% spot |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| nominal_100usd_eth_half | 11761329688889307/500000000000000000 | 3270000379082937824399/500000000000000000 | 2.360532% | 2.530888% | False | False |
| nominal_100usd_eth_full | 11761329688889307/250000000000000000 | 3228878872250881125531/250000000000000000 | 3.588386% | 4.966897% | False | False |
| nominal_5usd_eth_half | 117613296888893/100000000000000000 | 331004785463447209189/1000000000000000000 | 1.164748% | 0.128874% | True | True |
| nominal_5usd_eth_full | 2352265937777861/1000000000000000000 | 330791565350936423209/500000000000000000 | 1.228414% | 0.257498% | True | True |

The2% swap/1% spot settings above are the earlier recorded rehearsal settings, not newly chosen production policies. Total contribution remains3%, requiring97% actual marginal deployed LP; conversion1%, maintenance3%, additional execution1%, source agreement3% and idle checks remain distinct. A successful small growth-sized swap quote does not establish growth acceptance: actual active-NFT state, independent prices, whole operation, caller floors and gas remain untested here.

Alternative10018 pool9fa185… has moved further from selected spot. Better ETH-to-ZZZ token output cannot establish reference admissibility; route-matrix.json records its before/after conditional spot and each gross/fee-net floor separately. V3 fee1% quotes1000ZZZ to0.002561896473132607WETH, own-spot loss1.047203% and selected-reference loss27.049621%. V3 is an optional manual earned route only with a reviewed nonzero immutable wrapper chosen before seal, exact proxy/route/native+WETH+ZZZ prices, and full simulation. Wrapperzero cannot later gain v3, and fresh7 automated conversion remains native-v4-only.

Two native pools19820d…/07ee2b… offer favorable tiny reverse outputs versus selected spot, so this evidence does not claim every1%-floor quote fails.19820d fills0.001ZZZ to6,203,015,131wei ETH, but0.01ZZZ rejects incomplete input; captured current-range input capacity is0.003685802303845406ZZZ.07ee2b fills0.01ZZZ to36,249,908,446wei ETH but1ZZZ already loses about48.95% versus selected spot. Dust selected fills may also pass an integer-rounded point-vector output floor. None supplies independentUSD truth, economically useful gas, a genuine whole-NFT entitlement batch or full converter acceptance.

The replay port uses retained MIT Uniswap v4 integer math and45 bitmap/73 tick reads.138 main native responses and13 capacity responses match official outputs exactly;23 additional successful large/high-fee responses cross beyond the bounded captured words, so their postspot remains unavailable. Raw official quotes remain usable as output observations; no missing postspot is guessed.

Files: `route-matrix.json` (every direction/size/venue and conditional guard), `ROUTE_FINDINGS.json` (counts and boundaries), `quotes.json`, `small-capacity-quotes.json`, `tick-state.json`, `replay.json`, original raw request/responses, source pins and SHA256 manifest. No production tooling defect was demonstrated. The previous route collector had incomplete zeroL direction and enabled-fee coverage; this evidence-only collector closes those research gaps without production edits.

The final200,000-gas official-quoter recheck adds23calls:22outputs exactly match the earlier2M-gas quotes, including all selected native ETH vectors and13 positive capacity probes. The remaining100USD reverse-half alternative quote was already incomplete-input at2M; its200k wrapped empty error is retained. Same-budget official-quoter success does not qualify the distinct production Balancer wrapper/callback path, full transaction or converter gas. Total quote calls including these overlapping rechecks: **696**.

At the captured block basefee **20058000wei/gas**, even21,000 intrinsic gas costs **421218000000wei** before any conversion execution. The largest observed reverse output passing the correlated1% floor is **36249908446wei**, about11.62times smaller than that intrinsic-only basefee cost. This arithmetic is not an actual fee quote or paid cost, and no operating fee ceiling was selected. Actual keeper conversion uses whole selected NFT entitlements, not arbitrary slices manufactured from these input vectors.

These are external market quote depths. No PoPL deployed LP was withdrawn, and the evidence does not qualify remaining external depth after a future PoPL close or a future LP that dominates the market. Full-input semantics are authenticated in retained BaseV4Quoter.sol lines54–56: signed actual specified delta must equal the exact request or NotEnoughLiquidity is thrown. Empty-active-L cheap candidates retain191 decoded incomplete-input errors and19 other errors; the latter are not silently converted into proven no-liquidity findings.

Use **ROUTE_FINDINGS_FINAL.json**, **ROUTES_FINAL.md** and **final-manifest.json** as the final evidence pointers. Earlier derived findings/manifests remain intact as intermediate snapshots.

A further principal-only admission check does not need a chosen USD truth: target and balancing venue must share one ETH/fixedZZZ reference, and each has a hard500bps spot ceiling. Their reference bands overlap only when `max(P)/min(P) <= 1.05/0.95` (about1.105263). Here P is ZZZ-per-ETH from physical sqrt. Alternative10018 is about1.358280times selected P, so it cannot be admitted simultaneously with selected under any shared reference within that ceiling. Of the eight active principal-fee-compatible states, only selected itself and thin07ee2b have overlapping pre-swap bands. This is necessary admission geometry, not qualified price truth, a recommended500bps setting or a proof every possible contribution fails. It does not apply to the separate earned converter, which retains its own independent-price/output guards. `common-reference-bands.json` records all95 states.
