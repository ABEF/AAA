# Full normal claim admission and bounded prefix planning

20 November2026. Baseline main: `be5d3c75df1dcdfbd523abd0935ad37292c253d2`.
Trusted normal Solidity build remains `activation-final-six-20261118`,
Factory6/allocation2. **Production remains undeployed and NOT APPROVED.**

## Result

The new fixture runs the normal backend Projection and complete deployment,
portfolio, lifecycle, currency and final transaction checks. It replaces none
of those positive-path checks. It uses real sealed Access, real Registry, all26
API runtime pins,32 actual mint/Entry activations and65 royalty currencies.
The previous maximum-state fixture's admission replacement remains historical;
it is not relabeled as this proof.

A harder32-entry selection exposed a confirmed backend defect: after proving
healthy16- and24-entry prefixes, planning consumed its1,024-call allowance while
seeking a larger batch and returned no draft. The four-line production fix stops
at the **first successful prefix**, then performs complete fresh final
preparation. It preserves every remaining selection and all financial checks.

This deliberately favors producing a safely sized review over filling the
largest possible batch. It can require more claim transactions. The API never
guaranteed optimal batch packing; no claim is skipped, auto-submitted or queued.
Operators/users can explicitly select known healthy currencies rather than
repeatedly including a failed currency. An opaque revert is not a diagnosis.

The new current-source16-entry prefix passes full admission in885 RPC reads,
is actually paid within12M/full20%, and its remaining16 entries are freshly
planned with653 reads. The failed Tax currency keeps its exact entitlement.

## Actual stages and source boundaries

| Case | Source and measured result |
| --- | --- |
| Ordinary32 mixed entries | Original `6d5241…` planner; full normal admission,1 trial plus final,684 RPC,3.875s. Estimate5,107,263; full20%6,128,716; actual receipt4,254,663 gas. All32 selected rights pay once. |
| Fresh original32 zero replan | Original source;444 RPC,4.875s; every original entry zero, no draft or simulation trial. |
| Small healthy ERC20 claim | Original source;411 RPC,3.203s;220,029 estimated/264,035 padded;212,597 actual gas. |
| Small healthy+Tax selection | Original source;435 RPC,3.485s; healthy prefix pays, Tax singleton remains unavailable with1e18 units backed. |
| Required late-Tax32 baseline | Original source;1,024 RPC,8.719s; `WorkLimit(rpc_budget)`, no draft, despite proven16/24 prefixes. Preserved as the original failure. |
| First-success16 review | Current `7a3e720…` source;885 RPC,6.687s. Subsequent local pre-send estimate refuses because the restored pending clock is earlier than the confirmed opening time; no transaction sent. |
| Corrected-clock continuation | Same exact current graph/source, no constructor/population repeat. Full32 request publishes16 entries with885 RPC/6.562s. Actual16 payout estimates1,849,611 and submits2,219,534 with full20%, under12M. |
| Fresh remaining16 review | Current source;653 RPC/6.891s,8-entry next unsigned draft. The remaining Tax right is explicit and retained. This next draft is not automatically sent. |

Times are observed finite local request times, not provider or end-user latency
guarantees. Limits stay25seconds,1,024 logical reads,2,048 HTTP attempts,
32 selections,10 trials plus fresh final preparation and12M/full20% claims.
Fee-price, complete-fee declaration and wallet-funding bounds remain separate.
No source gas default or engineering allowance is raised.

The original ordinary32 source can be reused on its exact scope: an initially
successful complete selection already ended the old loop, so the new break
changes no executed selection/final-validation behavior for that path. Its
capture is still replayed under archived original bytes, never relabeled current.
New late-case positives replay the exact changed source. service.py, checkpoint
semantic sources, all Solidity/ABIs/storage and browser signing are unchanged.

## What was actually constructed and funded

- Real normal25-creation/19-binding graph,39 instances and112 binding checks;
  distinguish that construction inventory from the API's26 configured pins.
- All five external native runtime hashes exactly match Registry's immutable
  pins. Cached analyzed bytecode is truncated to its recorded original length
  before authentication. Fresh native constructor state and token funding are
  explicit local fixtures, not adopted public-chain storage or a supply proof.
- Ordinary configuration and real Access sealing occur only on the new owned
  chain. No existing/public contract is sealed, unsealed or replaced.
-32 new SeaDrop mints/draws and32 actual Entry activations, with controlled
  correlated ETH/ZZZ feeds and VRF. Activation input is0.055 test ETH, nominal
  $110 at the controlled publication; it is not qualification of live$100 routes.
  This fixture uses one physical main LP. The previous1,000-NFT/two-LP financial
  evidence retains its separate control-graph and source boundaries.
- Three bounded external-depth helpers each retain their100ETH maximum. Total
  actual external funding is268.328157299974762917ETH and
  536,656.314599949527137551ZZZ; unused budgets return. This synthetic depth is
  not current market liquidity. No guard is loosened to obtain a pass.
- Actual external trades and Vault harvesting create funded LP rights. Actual
  original-currency receipts fund royalty rights after the one-hour opening.
  Sixty-three conventional6-decimal currencies and one18-decimal taxed currency
  are deliberately admitted for fault testing:65 royalties including ETH,66
  asset descriptors including the separate fixed-ZZZ LP currency.

Worst tested Entry estimate is16,720,367/full20%20,064,441 under32M in this
32-active-NFT fixture. This does not replace the previous1,000-active-NFT
maximum-state evidence or close its slow-ZZZ opening shortfall.

## Independent verification and focused tests

The normal API verifier independently authenticates construction, exact runtime
and reciprocal bindings, full normal Projection replay, source-specific wire,
published calldata, estimates, padding, receipts and recipient deltas. Five
original-stage API responses, three refusals and two actual original-stage
payouts pass. Original32 entries pay exactly once; fresh replan is zero.

Eight new offline corruption controls reject altered runtime identity, an omitted
normal read, changed canonical header/caller, reduced padding, changed recipient
balance, forged source pin and erased Tax entitlement. The runtime-pin negative
changes configuration; unsealed/final-lifecycle negatives explicitly intercept
one response and retain the genuine upstream value. They are not claims that a
real sealed controller was unsealed or malicious governance was exercised.

The separate late-case verifier replays the original budget refusal under its
archived source and the new requests under current source. It binds exact-state
restoration, the actual16-entry receipt/current-owner payout,16 paid entries now
zero and16 unselected entries still positive. It does not trust a producer's
`normal_admission` flag instead of replaying the actual normal checks.

Three new focused methods and one updated affected existing method pass. They
check conservative prefix selection, complete fresh final validation and final
owner/lifecycle changes discarding earlier success. No unchanged test method,
contract/browser suite, old1,000-NFT population or normal build is rerun. The
test invocation was observed once; its receipt states that an independent raw
stdout file was not captured.

## Recovery-clock finding and its correction

Anvil's exact-state restore retained the confirmed future fixture header, but
its pending clock initially regressed before the royalty opening. Confirmed
simulation correctly passed while pending estimation correctly refused. This
was a local restore/clock problem, not permission to bypass the opening rule.

On the new owned continuation node, one explicitly dated empty block advances
the local pending clock. The state root and sender nonce444 remain unchanged.
A supplemental wire check binds pending closed → empty mine → unchanged state
root → pending open → nonce444 → first send. Three new offline corruptions reject
missing/reordered observations. No completed API or EVM case is rerun for that
supplement. This is not an instruction to manipulate a public-chain clock.

All owned nodes stop; successful cases have no pending submission. Early receipt
polling and invalid restore-flag attempts remain recorded as harness failures,
not financial passes or production defects. Whole current-state restoration
retains exact source, genesis, ancestry, runtime, nonce and state root; it never
transplants old-version protocol slots or re-mints the population.

## Evidence storage and remaining work

Repeated safety observations made the original setup wire352,968,569 gzip bytes.
Its lossless XZ publication is6,298,516bytes and independently round-trips the
exact1,568,472,867 expanded bytes, in original order. No record is pruned or
rewritten. Original gzip bytes remain in the external archive. Other captured
artifacts use a standard tar.xz archive with per-file hashes and roundtrip checks.
Verification is offline; unpack into a new folder and use the separately
published full wire with the checker's `--wire` option.

The roadmap owner is **P17 API security/admission**; the earlier LPQ03 index's
P16 reference was incorrect because P16 owns artwork/metadata.

Still open:1,000-active-NFT full-normal workloads and other search/fault orders;
production HTTP/retry/ingress/provider and complete-fee acceptance; actual
independent feeds and1%-eligible conversion routes; matching website/service
adoption; the476,135 estimated-gas reduction for the prior slow-ZZZ case;
production authorities/OpenSea/VRF/content and independent audit/release approval.
No public transaction, service/site rollout, journal/checkpoint replacement or
public-signing change is authorized or performed by source publication.
