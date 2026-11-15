# Manual LP failure diagnostics

Reviewed15November2026 against `aaf1423189e1f8436418540ef7cf85cbbccc9e29`.
This completes a source-only diagnostics milestone for schema1 Active B/C/D and
explicit schema2 Parked D. It authorizes no deployment or transaction.

## What improved

Previously almost every manual preparation failure reported one generic reason,
without its stage. Filesystem/reporting errors could also conceal that a complete
unsigned artifact already existed. The seven-action management tool already had
stage/reason handling; its pattern is now applied to the separate manual tool.

- **68 known local causes** retain ValueError/RpcError-compatible exception
  families and get bounded static explanations: action/input/profile, actual
  authority/lifecycle, custody/inventory/geometry/asset/venue, operation funding,
  retained protections, gas headroom/price/fee budgets, expiry and changed controls.
  Existing contract-wallet and incompatible-Parked-mask codes remain.
- **Ten precise stages plus an honest preparation fallback** distinguish
  input/configuration, confirmed snapshot, manifest,
  initial simulation, later snapshot/simulation, final canonicality, rendering
  and publication. Lazy lifecycle checks and split gas comparisons preserve the
  original short-circuit/read order. Composite head/deadline failures stay
  composite, rather than being asserted as proven expiry alone.
- **Unknown remains unknown.** Raw exception/revert/provider text is never parsed
  into a financial cause or echoed. Only typed local codes are trusted; a foreign
  exception cannot spoof a known blocker with a matching attribute. Remote RPC
  metadata is method/category/type/size allowlisted. Hostile or unhashable metadata
  and custom class names do not leak or break the formatter.
- **Output safety is explicit.** Existing paths, including dangling symlinks, are
  refused before input loading. The shared atomic writer is unchanged. Once
  writing/reporting starts, failure reports `artifact_publication_uncertain` and
  `output_may_exist:true`: a complete file can survive a later sync, cleanup or
  stdout failure. No output deletion, replacement, retry or transaction is assumed.

The [operator guide](../../docs/OPERATOR_MANUAL.md) and
[complete diagnostic table](../../docs/MANUAL_LP_PREPARATION.md#manual-lp-failure-diagnostics)
explain fields, causes, stages and recovery. The sole Todo records this completed
milestone while broader diagnostics and real operating qualification stay open.
Feature/release/roadmap/findings records and repository context are consistent.

## Preserved boundaries

Successful standalone manual artifacts and ordered RPC reads match baseline in
five concrete B/C/D/Parked cases. Twelve negative comparisons retain read order
and base exception families. No guard, optional-mask choice, caller floor,
deadline, gas/fee/work default, source requirement, retry, signing, nonce, journal
or authority change is introduced. No trigger/sample observation is promoted to
a new preflight eligibility refusal; empty no-swap routing and Active D's future
harvest lower-bound semantics stay.

Management shares this helper and pins its bytes. **New management source
commitments and review hashes therefore change**; calls taking that hash also
have different new provenance calldata. Targets/economic inputs/contract behavior
stay. Never rewrite historical artifacts, reviews or pending journals. There is
no automatic contract/runtime/profile, earnings-checkpoint or keeper-health repin.

## Actual verification and remaining work

**28 unique new focused methods pass in two source stages**, using the real
Projection/Reader with injected transport and temporary files. The initial27
pass before the final fallback-only correction; one new case verifies that
non-annotatable exceptions cannot falsely report input validation. The27 prior
methods/helpers and preparation/guard bodies are unchanged; no unchanged27
rerun is counted. Baseline failures, intermediate shapes,
five successful artifact/read comparisons and12 negative comparisons retain
their exact scope in [verification](VERIFICATION.md). Comparisons are not extra
independent features or old suite reruns. Two internal peer reviews found no
blocking implementation issue; this is not an independent security audit.

All61 production Solidity files and100 normal compiler inputs match existing
evidence; unchanged strict source pins are verified. No Solidity/compiler/static,
browser, older manual/Parked or broad Python suite was rerun. Four unrelated dirty
files remain byte-identical. Websites, signer/public-null settings, existing
Anvil, journals, services and the user-paused heartbeat were not changed.

Opaque helper/RPC/revert causes may still be unavailable, with no numeric code.
This tool cannot establish absent pending transactions, provider honesty, future
inclusion or universal financial readiness. Actual manual C/D/Parked EVM/gas,
complete provider fees, contract-wallet envelopes and operating qualification
remain separate release work. See the owning
[operation-review task](../../TODO.md#task-operation-review).
