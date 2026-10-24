# Keeper and bounded range policy: scoped verification

Internal candidate evidence only. **Production NOT APPROVED.** No signing,
running service, existing journal, local chain, website or public deployment was
changed. [Parent review](../REVIEW.md) and [operator guide](../../../docs/RANGE_POLICY_UPDATES.md).

## Harness improvements and actual results

Before changing keeper behavior, the new decoded-contract maintenance harness
reproduced ambiguous booleans/oversized limits, missing per-currency thresholds
and cooldowns, and obsolete bridge scheduling. The initial ten-case run observed
25 failing subcases and one legacy-route error; this was a diagnostic run, not
a passing regression. Later cases extend the harness to native idle/capability
bindings and the explicitly versioned adaptive policy.

[Final keeper receipt](keeper-final.json) records **277 passes and one explicit
Unix-only skip** across 278 distinct cases. The final run verifies source hashes
before and after execution. [Full log](keeper-final.log). Tests use decoded RPC
transcripts/mocks, plus the actual pinned `cast` help parser; they do not sign a
transaction or qualify Linux permissions, providers or an operating service.

An earlier complete run passed but the JSON recorder could not serialize the
Unix skip's test object. The [retained original log](keeper-final-recorder-repair.log)
and corrected final receipt distinguish an evidence-recorder repair from a
production failure. Repeated cases count once, not twice.

[Final range receipt](range-policy-final-summary.json) records **18 Solidity
passes**: nine new policy/orientation/callback cases and nine existing manual-range
cases. Each of the two fuzz properties completed 1,000 runs with zero failed
corpus replays. [Raw result](range-policy-final.json). The new endpoint property
checks independently cross-multiplied inequalities on actual Uniswap tick roots
at reference ticks and their one-unit neighbors, positive/negative ticks,
spacing 1/200, and 25%/50% widths. It does not copy the inverse-range rounding
formula being tested.

The range fixture executes the actual Registry, Strategy and dual-source Oracle
code with explicit mock governance/admission, token/feed and physical-position
observations. It does not execute venue settlement or qualify independent feed
providers. Installed-v4 settlement evidence is recorded separately by the parent
verification. The nine unchanged manual-range cases include actual sealed
AccessController governance; callback stop matrices use the explicitly identified
mock controller. The callback's consolidated authorization was separately checked
against actual `AccessController.moduleAuthorized`, which binds sealed state,
canonical state zero and the fixed Strategy identity.

## Normal size gates and source bindings

[Final size result](range-size.json) uses solc 0.8.26/Cancun, via-IR,
optimizer-runs 1 and Yul disabled, with unchanged EIP-170/EIP-3860 gates:

| Object | Runtime | Creation plus arguments | Result |
| --- | ---: | ---: | --- |
| Registry | 12,027 | 49,089 + 32 = 49,121 | Pass; 31-byte initcode margin |
| Strategy | 20,960 | 21,556 + 32 = 21,588 | Pass |

An initial full-modifier callback exceeded normal Registry initcode; consolidating
redundant controller reads still left a [62-byte overage](range-size-second-oversized.json).
The final callback uses the existing fixed-controller module authorization plus
explicit pause/preparation checks before local writes. It has no external
state-changing callback to recheck afterward. Removing the redundant Registry
event recovers the remaining bytes: the only authorized Strategy caller already
emits the successful old/new width and review hash atomically. No normal guard
or size ceiling was removed. The [first observed overage](range-size-oversized-observation.json)
is labeled as an observation because its original output file was replaced by
the justified source-change rerun; the second and final receipts retain complete
compiler settings/source hashes.

[Final bindings](final-bindings.json) match 39 keeper/code/test inputs, 47
range-suite inputs and all 42 production-source inputs in this two-object size
check. This is not a fresh full production build or full contract regression;
the parent verification records the combined final gates separately. No fork,
target-chain gas, external wallet or independent audit approval is inferred.

## Verified safety boundaries and remaining qualification

- New bridge scheduling is removed. Nonempty retired route configuration cannot
  authorize a new send. Existing pending receipts remain recoverable first;
  missing original fee evidence is never guessed, discarded or resent.
- Idle is opt-in, attributed per bucket, bounded per currency and subject to
  runtime/parent/version checks and both local/on-chain cooldowns. No raw-balance
  sweep or external cleanup recipient is added.
- Mode zero retains historical price direction. Mode one is explicit inverse
  token0/token1; existing physical LP ticks change only after normal maintenance.
- Automatic selection is disabled by default. Governance must provide reviewed
  thresholds, interval and review hash; source rules can select only 25%/50%.
  Fingerprints bind all other pool settings and orientation. Pending ticks,
  stops, canonical locks, bad prices or wrong runtime/capability fail closed.
- Current displacement and a cooldown do not prove historical volatility or a
  quiet market. Serial selection/rebalance latency, turnover, MEV, thin markets,
  gas economics and cumulative costs still need real strategy/operating review.

Actual assets, routes, feeds, governance addresses, provider/RPC qualification,
native website integration, gas/recovery rehearsals and independent audit remain
separate release gates. No option is enabled in an existing service by this work.
