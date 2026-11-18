# Feed engineering: equivalent valuation, preserved rejection

This is isolated source-copy engineering evidence, not adoption, a normal graph
build or full activation gas qualification. Baseline is commit633f015. During these isolated stages, ROOT
source, settings and the four protected dirty files remained unchanged. No live
RPC, service, wallet, chain or environment is used. All runs select only new
methods in an owned standalone project with the normal0.8.26/Cancun/viaIR,
optimizer1 and Yul-disabled settings. The1M harness size allowance is test-only.

## Candidate and proof

The uninstrumented [candidate](candidate/ZZZV4SpotPriceFeed.sol) consolidates
semantic `_state` checks into `_validateState` while retaining noncanonical
wide-word rejection before casts. Exact sqrt/tick/fee/minimum-liquidity and
downward-crossing consistency checks remain. Every configuration pin, external
call, ETH freshness/round check and source limit remains.

For decimal0<=d<=18, B=2^192 or2^128 and the unchanged branch ratioR:

`floor(floor(ETHUSD*10^d*B/R)/10^18) = floor(floor(ETHUSD*B/R)/10^(18-d))`.

This exact integer identity avoids inflating the intermediate numerator.
Any accepted final value is <=1e36, so both relevant intermediate quotients are
<1e54 and fit uint256. Valid accepted values and rejection/acceptance agree.
At impossible final values>1e36 the old larger intermediate can overflow before
its final guard; the candidate can instead reach `InvalidObservation`. Both
reject. A dedicated regression records old Panic0x11 versus the candidate's
error. Oracle's bounded-call wrapper maps either failed source to InvalidPrice;
no invalid price gains admission. This error-class change is explicit.

The three copied contracts have identical read-only instrumentation. Candidate
production names/comments omit it, so final normal source/runtime identity and
whole-activation gas require a fresh root-owned build. This record does not
relabel the instrumented artifact as an adopted runtime.

## Selected new checks and failures

Seven DISTINCT new methods have passing source-scoped evidence, not nine or
seven old-suite passes. Stage01 ran six: four passed (state crossings/bounds,
256-input tick fuzz, malformed wide responses and cold proof gas); two quote
methods failed because their original assertion incorrectly required identical
error bytes for impossible out-of-domain values. No accepted value mismatch
was found. Stage02 executed0 methods: compilation caught a diagnostic using an
old nonexistent Math error name; this OpenZeppelin version emits Panic instead.
Stage03 runs only the two changed quote methods plus one new explicit error-
class method: all three pass. It includes256 new quote-fuzz inputs and665
explicit decimal/sqrt/ETH-price boundary combinations. The prior four unaffected
method results are retained with exact feed source hashes and test-body scope.
Raw failures and selected output remain alongside successes.

## Cold proof benchmark and rejected alternative

Each proof call uses separately cooled feed/dependency accounts and slots.
The instrumented complete proof result has the expected320 bytes. These finite
measurements are not a promise for other market states or transaction layouts.

| Tick | Baseline | Semantic dedup + quote | Saved | Plus forward bracket |
|---|---:|---:|---:|---:|
|-200000|121154|112287|8867|121273|
|-1|107210|105842|1368|108249|
|0|107216|105849|1367|108296|
|1|107264|105896|1368|109001|
|200000|111215|109847|1368|116242|

The forward-bracket alternative replaces inverse tick validation with forward
boundary calculations. Its state equivalence checks pass, but its cost is worse
at every measured tick, so it is NOT proposed for adoption. The smaller selected
candidate saves1,367–8,867gas per tested proof; it does not demonstrate a1M
whole-activation reduction. Repeated call frames must not be summed across
inclusive nesting. Full20M/20% qualification remains the parent's separate work.


## Parent adoption and new boundary proposal

After these isolated measurements, the parent adopted the exact uninstrumented
feed candidate alongside its separately reviewed Oracle codec. That later source
is not the stage01/03 artifact, and its normal/complete-flow verification is
separate. Stage preservation statements do not claim that no parent source
adoption occurred later.

[Boundary selection](BOUNDARY_SELECTION.json) inventories nine older relevant
methods without rerunning them. It recommends the single strengthened
[NEW composite proposal](proposed/ActivationExecutionBoundary20261118.t.sol)
for the changed full-source graph: five deliberate callback faults in both
reference swap directions, complete rollback and a healthy fresh retry after
each direction. The proposal was not compiled or executed in this feed-engineering
stage; it is not an eighth passed method. Mock authority/feed/Permit2 and token
seams and its separate maximum-state accounting/gas limits are explicit.
