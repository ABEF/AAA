# Actual price and market feasibility — 20 November 2026

**The bounded read-only refresh is complete. No independent price pair or whole
PoPL operation is approved.** Current evidence still requires real publication,
source-independence and executable-depth decisions before launch. No source,
route, provider, limit or running configuration was adopted.

Source baseline: `519ff4f075022f789f46facbab56f0a944705b11`, `main`.
Owning packages: [P03–P04 in the roadmap](../../docs/ROADMAP.md#p03--independent-prices-and-reference-integrity).
The central Todo continues to own status; these observations do not close Q01.

## Fresh evidence and provenance

| Item | Observed scope |
| --- | --- |
| Chain | Robinhood mainnet4663, exact independent genesis pin |
| Anchor | `119000058`, `2026-11-20 11:01:08 UTC` |
| Hash | `0x2d9e3d565cef3714f0dbc40bb6ed0253adab8a1a1b41a3eb53b2a8fe93f87547` |
| State reads | EIP-1898 hash selector with `requireCanonical:true`; exact numbered header rechecked at phase end |
| Primary | 33 serialized HTTP requests,64.463494s,28 results and5 application RPC errors |
| Inventory |95 previously authenticated native-ETH/fixed-ZZZ/hookless PoolKeys through four bulk storage reads;95 is not the HTTP request count |
| Directional quotes | Six diagnostics inside the33 requests: three venues, both directions; two positive results |
| New-pool discovery | Three further HTTP requests,4.405128s; filtered Initialize interval `115708675..119000058`, zero events, canonical closure |
| Bounds | Each phase retains its original90s deadline,2s actual-start pacing,12s absolute HTTP cap,256KiB response bound, zero retries/no automatic fallback |
| Provider | Anonymous public Pinax endpoint, observed only; no SLA/capacity/archive/fee or adoption approval |

The first invocation under default network permissions stopped on one `URLError`
with no HTTP status, chain response or quote. Its exclusive output remains in
the archive. A separate tool-authorized network-capable invocation used identical
recorder bytes in a fresh directory. The successful36 HTTP calls are not merged
with that failed attempt into a fabricated successful provider campaign. There
was no HTTP refusal or rate-limit response in the successful phases; a refusal
would stop its phase without retry or range shrinking.

The primary recorder reuses the [16 November source](../real-market-refresh-20261116/REVIEW.md)
unchanged except for its exact current source-baseline label. Discovery reuses
its original logic/bounds with only the start anchor advanced to the already
closed16 November anchor. The offline analyzer is the exact earlier source;
the new wire-integrity check independently binds complete quote/feed/error and
header relationships. No old unit, Solidity, browser, static/compiler or13-check
RPC suite was rerun.

## Prices and operating-source requirements

| Source | Actual observation at the anchor | Meaning |
| --- | --- | --- |
| Chainlink ETH/USD | `$1,757.10340170`, publication age1,478s,8decimals | Structurally within the hard one-day ceiling; operating max-age remains unapproved. |
| Second checked Chainlink proxy | Same underlying aggregator `0x6091e64eb7138eef066a80fd3a0d7427b91f2721` | Another proxy is not an independent second ETH source. |
| Stored Pyth ETH | `$2,241.72518`, age1,147,315s;2,758.072051bps disagreement versus Chainlink | Fails the hard86,400s age and300bps agreement checks. No update/publication/funding occurred. |
| API3 ETH | `read()` reverts with `0x8086c764` | No usable observation. Current name/base/subscription is not refreshed; the precise cause is not inferred from the revert. |
| Fixed ZZZ | No independently qualified source pair established | Pool-derived conditional prices and external listing leads are not approved USD sources. |

Current [Pyth sponsored-feed documentation](https://docs.pyth.network/pro/sponsored-feeds)
does not list Robinhood among its sponsored EVM networks. A supported
[contract/interface](https://docs.pyth.network/pro/contract-addresses) therefore
does not establish timely publication: a reviewed publisher, transport/data
access, gas funding, alerting and recovery arrangement is still needed. Core
stored-price and Pro per-transaction verification interfaces remain distinct.

[API3 operation](https://docs.api3.org/dapps/integration/) requires a funded
service with suitable update terms and renewal. Its documented standard24-hour
heartbeat and three-month mainnet plan do not establish current activation or
adequate operating headroom. Its [round compatibility guidance](https://docs.api3.org/dapps/integration/aggregatorv2v3interface.html)
explicitly distinguishes asynchronous updates from meaningful Chainlink rounds;
PoPL's current round checks require reviewed adaptation, not weaker validation.

The user-selected **spot for placement and independent valuation** remains.
Two different ETH feeds multiplied by the same ZZZ pool still repeat the same
ZZZ exposure. A fresh block or fresh ETH answer does not establish a recent ZZZ
trade; stored slot0 has no last-trade timestamp. No TWAP, single-source fallback,
new independence ID, max-age, review hash or service selection was invented.

## Execution and selected-destination feasibility

| Venue / direction | Diagnostic result | Boundary |
| --- | --- | --- |
| Selected `0x501122…afe1b`, ETH→ZZZ | Full nominal$100 ETH input returns output;14.699808% gross loss versus its own starting spot,13.750197% additional loss after known fees | Fails necessary3%/additional1% analytical screens. This is not the strategy's computed swap fraction. |
| Selected,1,000ZZZ→ETH | Exact-input quote reports incomplete input | Does not qualify that reverse size. |
| Largest known raw-active-L `0x012aa4…3e551`, ETH→ZZZ | Full nominal$100 ETH input returns output;1.661089% gross loss,0.567430% additional loss | Passes those pointwise analytical screens against its own starting spot only. |
| Largest known raw-active-L,1,000ZZZ→ETH | Exact-input quote reports incomplete input | Forward success does not prove bidirectional execution or default1% LP conversion. |
| Low-fee95pips candidate, nominal$5 ETH→ZZZ and1,000ZZZ→ETH | Empty wrapped reverts under the unchanged500k diagnostic ceiling | Cause remains unknown; not a proved liquidity-only failure. |

The selected pool still has **zero current active liquidity**. This does not
prove that all distant initialized ticks are empty. The largest known raw-L
candidate's stored ETH-per-ZZZ price is approximately **5.811926 times** the
selected pool's price. Their ordinary maximum500bps reference bands cannot share
a valid price at this anchor. A usable forward quote on the larger venue does
not make the chosen destination/reference combination executable.

Thirteen known pools have nonzero active liquidity and pass the separate
reference fee-only screen; seven pass the stricter principal fee-only screen.
These are not ownership, TVL, depth or independence approvals. The larger venue
currently charges10,999pips combined directional fee; its raw liquidity ranking
is not a global best-execution or highest-TVL guarantee.

The nominal$100/$5 ETH diagnostics use the single observed Chainlink answer for
sizing. They are not qualified contribution valuations, assumed50/50 swaps,
marginal LP measurements or complete Entry/Vault simulations. Quoter output/gas
does not provide the authenticated post-state required by LP3. No production
deployment exists here; complete activation/growth/maintenance/conversion remains
unqualified on these actual markets.

## Fixed token and inventory continuity

Fresh fixed-ZZZ runtime is3,248bytes with Keccak
`0x3d5ba33c3a94f655c16348011ff2c72f6ce8085239454ce4a6c4bf284e84a597`,
matching the prior authenticated runtime. Exact raw evidence is
`approved-transport/capture/rpc-07.raw` in [evidence.zip](evidence.zip), SHA256
`213ebff164fb37fb87d6646080e4d0d2c86b5e464e9403716bc0c26fd4c28c79`.
This binds outer runtime at the canonical anchor; actual admin/source/burn/control
review is a separate source-qualified task, not inferred from the token symbol.

The three-call Initialize query extends the previously recorded filtered interval
from16 November through this anchor. No new same-core/native-ETH/fixed-ZZZ keys
were returned. This does not prove provider-complete logs, global highest TVL,
other cores/versions/pairs or absence of private/custom price products.

## Concrete remaining inputs

1. **ETH secondary:** choose a supported authenticated Pyth publication operation,
   an activated API3 service with separately reviewed compatible adaptation, or
   another actual independent supported proposal. Establish fees, publication
   responsibility, maximum ages, monitoring, renewal and recovery before admission.
2. **Independent fixed-ZZZ truth:** identify two genuinely defensible valuation
   paths with exact markets/contracts/reporters and common-mode/manipulation
   review. Reusing one pool twice cannot close the requirement.
3. **Market execution:** establish sustainable bidirectional external depth and
   a compatible selected-destination/reference configuration under current
   guards. Selected pool changes or real liquidity funding require separate
   operator decisions; neither was performed here.
4. **Complete operation:** only after those inputs exist, qualify actual current
   F6 ETH/ZZZ activation/growth,97% marginal deployed LP, reward conversion and
   maintenance with32M/full20% and24M/full25%, complete fees and exact source proofs.

## Evidence verification and unchanged boundaries

[RESULTS.json](RESULTS.json) exports exact rational prices, fees, outputs/errors,
candidate states and limitations. [PRIMARY_SOURCES.json](PRIMARY_SOURCES.json)
is a dated reference index, not an HTML or service-approval archive.
[VERIFICATION.json](VERIFICATION.json) records offline raw/header/source/feed/quote/
discovery binding; it is not a count of passing application tests.
[EVIDENCE_MANIFEST.json](EVIDENCE_MANIFEST.json) pins all61 archive members,
including60 individually hashed source/raw/failed-attempt files. Read archived
helpers before independently executing them; the analysis checker makes no
network call and does not mutate chain state.

Production code, compiler, financial safeguards, gas defaults, permissions,
signer, all existing Anvil/DB/checkpoint/journal state, websites/services and the
user-paused heartbeat are unchanged. No key, subscription purchase, commercial
provider engagement, transaction, deployment, seal, adoption or independent
release approval was involved.
