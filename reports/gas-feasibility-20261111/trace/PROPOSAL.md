# Measured execution-cost targets, before changes

Baseline `db509fbf4e357e5aec1d614ce66923fea0594d7e`. This is offline analysis of
existing final traces and current source, not another feature-test run, provider
probe, optimization result or permission to loosen a guard. No Solidity changed
in this partition. The parent coordinates any implementation/build work.

## Do not mix the measurements

| Scope | ETH activation | ZZZ activation | Meaning |
| --- | ---: | ---: | --- |
| Earlier prototype attribution |16525422|16858851| Before the final selective transient loader; not current cost |
| Final controlled cold fixture call |15317541|15644361| Existing final source-scoped harness result, excludes transaction intrinsic |
| Final actual-owner local RPC trace |14780416|14995485| Existing current synthetic-market callTracer result |
| Same actual-owner RPC estimate |15434990|15774271| Distinct estimator result, not an actual public receipt |
| Estimate plus full20% |18521988|18929126| Existing unsigned diagnostic envelope; default12M rejects |

Actual-owner growth RPC trace/estimate: ETH13594955/14317340,
ZZZ13829824/14642230. Existing final cold-fixture growth calls14103737/14404957
have a different warmed/test-wrapper context. None of these establishes a
Robinhood limit, execution/data fee or actual qualified market outcome.

The offline parser checks all61 current production raw source hashes against
each of the four retained RPC fixtures. It derives method names from the saved
normal compiler ABI, without recompilation. Full attribution remains under the
external evidence directory; the compact [metrics](FINAL_METRICS.json) retain
input hashes and scopes.

## Current trace hotspots

Native activation, final actual-owner RPC trace:

| Current method/group | Calls | Inclusive gas | Signed gas after immediate children |
| --- | ---: | ---: | ---: |
| Oracle.validateExecution |14|3965659|1539411|
| Both readers' executionProof |44|3132274|2748242|
| Oracle.executionBounds |34|1009766|802298|
| Oracle.executionReferenceX96 |12|439644|366420|
| Access.module |375|506500|506500|
| Access.protocolPolicy |329|334948|334948|
| ProtocolPolicy.sourceCallGas |242|133406|133406|
| PortfolioPolicy.range |13|580177|580177|
| Math.policyFingerprint |11|1832720|323584|

Inclusive costs overlap and must not be summed. Reader work and bound getters
are descendants of several full validation/fingerprint calls. RPC refund
accounting produces one negative signed residual at the root Entry frame; it
is preserved, not forced to zero or attributed as negative work to a helper.
The selected view-method residuals above are nonnegative. Signed residuals over
the complete tree reconcile exactly to each root's gasUsed.

## Proposed order

### 1. Make the transient codec cheaper without changing validations

`Oracle._loadExecution` currently copies49 transient ABI words into bytes and
runs the compiler's nested Execution decoder. `_loadQuote` loads15 words but
still constructs the full nested Execution memory object. Full proof boundaries
and header reads dominate measured Oracle-only work.

Proposed experiment: a compact Quote struct for the15 needed words; for complete
loads, typed assignments from named **static ABI word offsets**, following the
existing selective loader pattern. Keep the exact49-word/1568-byte wire, owned
canonical writer, length validation, full clear and all controls, pending state,
core/source/market/round validation. No handwritten Solidity memory-layout offsets,
no external writer and no live-price cache. Removing the unused full generated
decoder may also recover runtime space, but both cost and bytecode effects require
measurement; neither is established by this report.

Required proof: every context field equals canonical encode/decode at all states,
including both reference slots, equal pool IDs on distinct cores, signed ticks,
loan/destination/pending flags and relaxed nonreference-destination liquidity.
Unknown assets, pending swaps, changed/restored controls and late callbacks must
retain their rejection. The public observational Oracle methods remain live.

### 2. Hoist the source-call gas limit inside one STATIC chain

Each `_boundedRead`/`_boundedExecutionRead` independently rereads
`Access.protocolPolicy()` and `sourceCallGas()`. There are242 source-gas getter
calls in this final native activation trace. Within one full validation or one
observational read chain every downstream source call is STATIC, so the policy
cannot mutate between those reads.

Load the limit afresh once at that chain's entry and pass it through the private
read/round/market helpers. Keep the same per-source call ceiling, exact return
size, source pins, freshness/agreement and final control proof. Do not retain the
limit across a token/Core/recipient callback or cache it for an entire transaction.
The getter descendants alone suggest roughly0.34M removable work before call
overhead, not a measured saving or a5M solution. Shared private bounded-call code
may help the Oracle's88-byte runtime margin; normal limits remain mandatory.

### 3. Factor immutable reader data, retaining every live proof

The two executionProof implementations account for2.748M signed self work.
`_configuration` reloads constructor-only Config storage, then validates four
runtime pins, token/feed decimals and StateView parent. It is a promising
measurement target, but callTracer cannot separate internal copying from quote,
tick validation, hashing and ABI work.

Constructor immutables or a smaller exact configuration representation may avoid
repeated fixed storage/copy work. Preserve the config getter's values, the exact
round-ID formula, all four runtime checks, current decimals/parent, exact current
tick/L/fee validation, current ETH round and both captured/live quote calculations.
A differently hashed precomputed round domain would change observation identity
and is not a behavior-preserving optimization. No configuration reuse may replace
current market/ETH/source data.

### 4. Consider only proven STATIC-adjacent validation coalescing

The clearest candidate is `Pricing.endEntry`: `_unchanged` performs a full proof,
then `_clear` immediately calls `Oracle.endExecution`, which performs another
full proof. Only STATIC reads and local hashing occur between them. The original
earlier full call costs about289776gas in this trace. A scoped refactor could
retain every mark/policy comparison and the mandatory final full proof while
coalescing that duplicate. All other `_unchanged` call sites need their existing
full validation.

Manager has analogous candidates: beginManagerExecution followed by the initial
balance-context proof before the first token pull, and final balance-context proof
followed by STATIC fingerprint/spot checks and endManagerExecution. Every swap,
mint, increase, borrowed/owned context and emergency path must be checked before
using a fingerprint-only private form. No public context getter may become an
authority grant. Do not remove post-pull, post-settlement, post-refund or final
whole-operation checks merely because their current fixtures agree.

## Completion and limits

Rankings identify measured old work, not promised savings. Even a worthwhile
reduction may leave cold operations outside the default12M with20% headroom.
Current qualified target-chain block/transaction/RPC/fee data and existing optional
policy2 feasibility are separate work. Meaningful real external depth, independent
sources and actual dependencies remain required. Do not rescue a failed quote by
loosening source, financial, custody, accounting or user limits.

After an approved implementation, use one bounded current-source comparison of
the affected complete operation, necessary adverse controls and exact standard
size gates. Reuse unchanged verification; do not rerun broad suites for display.
