# Real ETH/ZZZ market and provider refresh — 16 November 2026

**No independent production price pair or complete transaction path is qualified.**
This pass completes a bounded observation milestone, identifies a better forward
execution lead, closes a gap in the recorded pool-discovery interval, and updates
the owning Todo/operator requirements. It does not enable a source or route.

Source baseline: `0b31f3300d85d1a8ea86e958759a97a006c5b67f`, `main`.
Current contract behavior, financial limits and all live environments are unchanged.

## Scope and anchor

The authorized work was fresh, read-only qualification of ETH/fixed-ZZZ sources,
activation/growth execution and ZZZ-to-ETH LP-reward conversion. Existing
construction, EVM, browser, compiler, static-analysis and 13-check RPC suites were
not rerun. No PoPL deployment exists in this capture, so no complete PoPL action
could be simulated against these actual markets.

| Item | Captured evidence |
| --- | --- |
| Chain | Robinhood mainnet, `4663`; chain/genesis checked |
| Anchor | `115708674`, `2026-11-16 10:57:04 UTC` |
| Hash | `0x511e1533b62a0921e2b3723e5edcb95617621b0ec0fb7e7c184dbb59d5157b22` |
| State reads | Exact EIP-1898 hash with `requireCanonical:true`; numbered header rechecked at phase end |
| Provider | Anonymous public Pinax endpoint; observed, **not adopted** |
| Actual work | 33 primary requests, 3 recent-discovery requests, 3 discovery-gap requests |
| Responses | 39 total: 34 results, 5 application-level RPC errors; no HTTP refusal or retry |
| Bounds | Each phase: at most 90 seconds, serialized requests at least 2 seconds apart, bounded response/body/time; no automatic fallback |
| Duration | Primary 64.382494s; recent discovery 4.347493s; gap 4.369041s |

Canonical closure is not a finality guarantee or a fresh twelve-confirmation
claim. A successful bounded read does not approve provider capacity, historical
state retention, logs completeness, tracing, SLA, hosting or full PoPL fees.

## Fresh source observations

| Candidate | Observation at the anchor | Qualification boundary |
| --- | --- | --- |
| Chainlink ETH/USD | `$1,806.42727821`; publication age 1,752s. Both checked proxies still resolve to aggregator `0x6091e64eb7138eef066a80fd3a0d7427b91f2721`. | One service, not two. Operating max-age, upstream/common-mode controls and correct-chain liveness remain unapproved. |
| Pyth stored ETH | `$2,241.72518`; age 801,471s; disagreement 2,409.717275bps against the Chainlink observation. | Fails the unchanged hard 86,400s age ceiling and intended 300bps agreement. No price publication/update/funding occurred. |
| API3 ETH | Current `read()` reverts with `0x8086c764`. | No usable observation. Current base/name/subscription was **not** refreshed; earlier zero-state observations retain their 13 November scope. Round-compatible adaptation remains unqualified. |
| Fixed ZZZ | No two independently qualified USD paths established. | Exact-token markets and external spot composites remain candidates; no fabricated direct feed, independence ID, max-age or review hash. |

The immutable optional reader may combine an independently reviewed native-v4
ZZZ/ETH spot with ETH/USD. This preserves the user's explicit spot choice; no
TWAP is added. Two different ETH feeds multiplied by the same ZZZ pool repeat
the same ZZZ manipulation exposure. A recent block or fresh ETH publication does
not prove a recent ZZZ trade: native-v4 slot0 is a stored price with no last-trade
timestamp. Raw active liquidity, TVL, usable external depth and truthful price
discovery are different properties.

Current provider documentation exposes operational work, not automatic admission:

- Robinhood is absent from Pyth's documented sponsored EVM feed list. If choosing
  the compatible Core reader, arrange a reviewed authenticated publisher, data
  access, gas funds, age alerts and recovery. Core and Pro interfaces differ.
  Documented zero verification fees do not make API/data, gas or operation free.
- API3 offers an ETH activation lead. Its documentation describes mainnet plan
  expiry after three months and a standard 24-hour heartbeat; neither proves a
  current funded subscription or sufficient freshness headroom. Its native round
  semantics require reviewed adaptation, rather than removal of Oracle checks.
- Public catalog research identifies no new authenticated exact-token ZZZ pair.
  This is not proof that a custom/private product is unavailable. Earlier catalog
  counts and CEX order-book observations are historical, not refreshed totals.

See [dated primary references](PRIMARY_SOURCES.json). No commercial provider
engagement, installation, selection, funding or payment occurred. No credential/API key was used.

## Markets and useful-size directional diagnostics

The exact token remains `0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a`.
All 95 previously recorded hookless native-ETH/fixed-ZZZ PoolKeys were reread
at the anchor. Seven active pools pass the **strict principal fee-only** screen;
thirteen pass the separate **reference-reader fee-only** screen. These are not
liquidity, independence, route or source approvals. High-fee reference candidates
can have poor arbitrage/price-discovery incentives.

Six new diagnostic quotes cover three venues in both directions. Nominal
`$100-sized`/`$5-sized` ETH inputs are floor-rounded using the single observed ETH
answer; they are not qualified contribution values or assumed strategy swap
fractions. The 1,000-ZZZ reverse input is an explicit raw-size diagnostic.

| Venue | ETH → ZZZ | 1,000 ZZZ → ETH |
| --- | --- | --- |
| Selected `0x501122…afe1b` | $100-sized input fills. Gross loss versus its own stored starting spot: **14.6770%**; additional loss after actual directional core fees: **13.7271%**. Fails necessary 3%/1% analytical screens. | Exact-input quote reports incomplete input. |
| Largest known raw active-L `0x012aa4…3e551` | $100-sized input fills. Gross loss **1.6459%**; additional loss **0.5520%**. Passes those pointwise screens against its own stored starting spot. | Exact-input quote reports incomplete input. |
| 95pips low-fee lead | $5-sized diagnostic returns an opaque wrapped revert. | Opaque wrapped revert. Cause unknown. |

Actual directional combined fees, raw amounts, errors and exact rational
calculations are retained in [RESULTS.json](RESULTS.json). Known fees are separated
from additional execution loss; a fee alone above 1% does not prove all routes
impossible when reference/venue prices differ favorably.

These quotes use a **500,000-gas read-only diagnostic ceiling**. It is not an
operating quote/transaction budget change or proof of success within a configured
production solver's smaller bound. Quoter-reported gas is not full PoPL gas or a
complete network-fee estimate. Successful quotes contain output/gas, not the
authenticated post-state and full LP placement required for actual execution.

The selected pool still has **zero current active liquidity**. This does not prove
that all initialized distant ticks are empty. The larger known pool's stored
ETH-per-ZZZ price is approximately 5.81193 times the selected pool's stored price;
their ordinary maximum-500bps reference bands cannot share a valid price at this
anchor. A favorable forward quote does not repair that incompatibility.

Consequently, this pass qualifies neither full $100 activation/$5 growth nor a
complete tested 1,000-ZZZ reverse/default-1% reward-conversion path. It does not
rule out other sizes, pools or later market states. Nothing is switched, given
synthetic liquidity, repriced to an assumed peg or admitted with weaker guards.

## Inventory gap closed, with explicit limits

The previous 95-key inventory derives from the 9 November scan ending at
`110324511`. Extending only the 13 November anchor would have missed an interval.
Two exact same-core/native-ETH/fixed-ZZZ `Initialize` queries now cover:

| Inclusive interval | Returned events | Header closure |
| --- | --- | --- |
| `110324512` → `113296579` | 0 | Exact retained 13 November header, before and after |
| `113296580` → `115708674` | 0 | Exact fresh anchor, before and after |

This stitches the **recorded filtered scan** to the new anchor. It is not a
proof of provider log completeness, coverage of other cores/versions/assets,
global highest TVL or independent externally controlled depth. No new keys were
authenticated by the separate public web research. [Coverage](DISCOVERY_COVERAGE.json).

## Required decisions and evidence

Existing task IDs remain the sole status ledger; none is closed by observation.

| Owner / task | Concrete next input | Evidence needed before admission |
| --- | --- | --- |
| ZZZ team + engineering: [creator pricing](../../TODO.md#task-creator-zzz-price) | Two genuinely independent exact-ZZZ valuation paths; direct USD or reviewed external ZZZ/ETH × ETH/USD | Exact contracts/PoolKeys, reporters/markets, controls, publication behavior, external liquidity and manipulation/common-mode review. |
| Operator + engineering: [source qualification](../../TODO.md#task-dual-price-qualification) | Choose an operating ETH secondary: compatible authenticated Pyth publication, or activated API3 with reviewed adaptation, or another supported proposal | Actual terms/fees, responsible updater/funder/renewal, age/liveness policy, monitoring and recovery; both sources must pass unchanged checks. |
| ZZZ team + engineering: [market liquidity](../../TODO.md#task-creator-input-liquidity) | Sustainable bidirectional external depth and a selected-destination price-compatibility plan | Actual direction/size quotes, residual depth after PoPL withdrawal, token/core controls and full-operation execution. No automatic pool change. |
| Engineering + operator: [contributions](../../TODO.md#task-activation-assets), [LP conversion](../../TODO.md#task-lp-eth-settlement) | Reviewed actual release configuration once those inputs exist | Full ETH/ZZZ activation/growth, 97% marginal deployed-LP proof, reverse conversion, source/control/callback checks, 20M/24M profile limits and complete fees. |

No service or route needs to be enabled merely to produce another report.
The operator [pricing procedure](../../docs/OPERATOR_MANUAL.md#configure-stop-and-recover-usd-pricing---2026-10-24)
now distinguishes observations, manifests, source admission and operating adoption.
[CANDIDATE_CONFIG.json](CANDIDATE_CONFIG.json) deliberately retains null policy
fields, empty routes and `deployable_configuration:false`; it is not an installer.

## Verification and retained evidence

The new collector has four mocked transport methods with recorded source stages:
three passed initially; one exposed Windows coarse monotonic-clock pacing and was
fixed using a high-resolution clock. An intermediate fixture timing-margin error
and its correction are retained. Only the affected method was rerun; the three
unchanged methods were not. The frozen capture source preceded every actual read.
[Producer stages](PRODUCER_STAGE.json) records the exact counts and hashes.

Independent offline review recomputed PoolKey/storage packing, source answers,
directional fees, output/loss fractions, quote errors and discovery boundaries.
The public bundle includes original serialized request/response bytes and source
pins. The verifier reads evidence only; it cannot submit a transaction or change
configuration. See [verification details](VERIFICATION.md).

All 61 production Solidity files, the eight prior deployment preparation/rehearsal
files and four unrelated dirty files are preserved byte-for-byte. Prior artifacts
retain their hashes/scopes. No unchanged tests, compiler, static analysis or local
deployment were rerun. No public transaction, seal, signer, local-chain call,
journal adoption, website/server rollout or heartbeat restart occurred. Public
signing remains disabled, both sites are unchanged, and production remains
**NOT APPROVED**. Qualified markets/services, actual operation and independent
audit remain release requirements.
