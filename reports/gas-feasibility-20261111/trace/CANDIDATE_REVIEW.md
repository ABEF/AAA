# Isolated Oracle gas candidate: review before acceptance

Baseline: `db509fbf4e357e5aec1d614ce66923fea0594d7e`. This partition prepared and verified an isolated candidate. Root subsequently
applied its exact LF source after independent review. Default budgets, financial
protections, public ABI, storage layout and capability versions remain unchanged.
The final candidate fits standard limits; complete operating feasibility remains
a separate decision.

## Retained implementation

The original full `Execution` object, compact-read return type, compiler-generated
49-word decoder, canonical encoder, transient length checks and complete clear
remain. The manual full-codec and smaller-Quote experiments were rejected when
they exceeded the normal size limit. Original failed builds remain in the external
candidate directory and are indexed in [CANDIDATES.json](CANDIDATES.json).

The final `oracle-gas-only-v3` candidate makes two behavior-preserving changes:

1. Each `_captureExecution` or `_validateExecution` invocation reads a fresh
   `sourceCallGas` once and passes it through that single entirely STATIC private
   read chain. Ordinary public/configuration paths pass sentinel zero, retaining
   the existing fresh lookup at each bounded read. No gas limit is stored or
   retained across a mutable callback, a whole transaction or a later validation.
2. `_agreedBounds` obtains the minimum and maximum using one comparison instead
   of separate `Math.min`/`Math.max`. For `a>b`, it assigns `(b,a)`; otherwise it
   assigns `(a,b)`. This equals the original result for every `uint256`, including
   equality. The exact spread subtraction and `Math.mulDiv` acceptance test remain.

The source-call gas cap, exact response lengths, bounded copy, domain errors,
source runtime/decimals/round/freshness checks, sequencer checks, live agreement,
core/StateView/pool identity, expected transition and late venue-state checks all
remain. The seven-control predicate and its order are byte-identical. Public
observational prices remain live; captured values have no new authority.

A source-gas limit cannot change inside the hoisted chain: each descendant is
STATIC, including the fixed Access/Policy, token/feed and StateView reads. The
limit is reacquired at the next complete validation, so this optimization does
not assume that settings remain unchanged across token, core or recipient calls.

## Measured fit and equivalence

One final full normal build uses the exact original Solidity 0.8.26/Cancun,
via-IR and optimizer settings, with a 100-source closure and 61 production files.
All 48 normal gates pass. Oracle runtime is **24,573 bytes: only 3 bytes remain**;
this is 85 bytes larger than baseline. Its creation object is 48,466 bytes,
48,530 including the 64-byte constructor arguments. Other production runtime and
creation objects are byte-identical. Vault remains 24,544 bytes / 32-byte margin.

The read-only comparison checks all 191 production ABI entities and normalized
storage descriptions: all remain identical. Oracle-only fitting and final full
build produce identical Oracle creation/runtime bytes. The following private
functions are byte-identical: full load, header load, save, clear, length,
caller authentication, execution controls and wide round decoding. The number
and position of full execution-validation boundaries are unchanged.

Compiler input SHA-256:
`7741d92ee499a2a8bdda9ae234ffcb474e34518bb0196390d1a0d70079c68b0c`.
Compiler output SHA-256:
`27b773bc781f9cc9f9f4583fa8a9cdaf380c7e7c58eff0a867090a1f3ffa5012`.
The full normal, `EQUIVALENCE.json`, original failures and source diffs reside in
`V/gas-feasibility-20261111-db509fb/trace/candidates/`.

The frozen LF candidate hash is
`2b1e52432d497add746bbaace8fee950969e40ee885a069f2074712221bf29aa`.
Its prospective CRLF landing copy hash is
`7f8749914e461813a61fb9b235e7e848914826f45edf40f2449d373af129303f`.
`EOL.json` retains an intermediate prospective CRLF copy and only proves
normalized text equality. That copy was **not** the final landing: exact raw
compiler-content binding takes precedence, including compiler metadata. Root
applied the original LF candidate `2b1e...`. The final published source manifest
and landed-source binding verify that all100 current raw files equal the
accepted compiler input byte-for-byte, with no EOL normalization or recompilation.
Other60 production raw sources remain unchanged.

## Measured benefit and remaining feasibility

The focused [execution receipt](../verification/EXECUTION.json) records23 actual
EVM methods with `Success`:18 affected methods and5 new maintenance methods.
The wrapper failed during artifact postprocessing after Forge completed; the
original exit1 is retained. The receipt derives individual statuses from the
original saved output, without another compiler/EVM run. An expected strict-budget
rejection inside a passing method remains a rejection, not a successful12M call.

The like-for-like cold-fixture [gas results](../verification/GAS.json) show:

| Operation | Baseline call gas | New call gas | Saving |
| --- | ---: | ---: | ---: |
| ETH activation |15317541|14636780|680761 /4.44%|
| ZZZ activation |15644361|14963971|680390 /4.35%|
| ETH growth |14103737|13422920|680817 /4.83%|
| ZZZ growth |14404957|13724583|680374 /4.72%|

All four exact12M calls still reject. Their full20% review envelopes are
17.56–17.96M for activation and16.11–16.47M for growth. These are controlled
1000USD diagnostic contributions, not real market/current100USD acceptance,
RPC estimates, public receipts, transaction intrinsic gas or network data fees.
The retained old actual-owner RPC figures remain baseline-scoped and were not
reinterpreted as new-source measurements.

New full-operation maintenance measurements are a separate one-activated-NFT
cohort, not a before/after optimization comparison or1000-NFT worst-case bound.
Single/two-leg harvest uses0.661M/1.016M raw call gas. Compound uses10.681M;
ordinary single rebalance13.448M; hybrid open/replacement16.324M/16.632M.
Compound fits a raw12M call but exceeds it after the keeper's separate25%
headroom. These operations therefore retain distinct readiness/blocking outcomes;
frontend20% and keeper25% are not interchangeable.

The old final ETH-activation trace contains242 source-gas getter calls. Source
inspection predicts about30 after hoisting:22 fresh complete capture/validation
chains, four separate venue reads and four ordinary value reads. This count is
still a source/old-trace prediction, not a new callTracer measurement. No composite
proof or complete validation boundary was removed.

The runtime gain is an operating-cost improvement, not production approval. The
Oracle's3-byte margin, unchanged12M defaults, realistic current contribution
amount/depth, independently qualified feeds/routes/providers and complete target
operation acceptance remain explicit. No further fit experiment is planned here.
