# RPC preparation capabilities: scoped verification

Baseline: `8cec66c`. This slice extends the existing read-only probe rather than
adding a second service tool. It changes no Solidity or financial policy.
The [receipt](receipt.json) records exact final source hashes, Python version,
commands/scopes and evidence limitations.

## Implemented improvement

- Unknown canonical-block rejection requires recognized sanitized remote
  missing-block metadata. Timeout, rate limit, invalid parameters and ambiguous
  remote errors cannot turn unavailable service into successful qualification.
- Explicit `activation_api_v1` checks independently reviewed genesis/runtime
  and an actual exact `Approval(0)` witness from same-hash `eth_call` and
  `debug_traceCall` with `callTracer`/`withLog`. These simulations persist no state
  and use no overrides, user approval, signing or PoPL deployment.
- Unavailable first-endpoint reference history no longer suppresses observations
  for the remaining endpoints. Reports keep public diagnostics, JSON-RPC error
  metadata and actual HTTP statuses separate; provider messages/URLs are omitted.
- CLI configuration is bounded and rejects duplicate/nonfinite JSON, input
  overwrite and unsafe diagnostic echo. Reviewed runtime mismatch stops tracing.
- The 100-logical-call bound is demonstrated, as is rejection of replies arriving
  after 90 seconds. The deadline is not a hard watchdog on an in-flight transport.

See the [operator procedure](../../docs/RPC_PREPARATION_QUALIFICATION.md) and
[dated official-source research](RESEARCH.md).

## Evidence actually executed

The original baseline probe was loaded in isolation without reverting the work
tree. One new method produces **four expected failed subcases** for false
qualification; its [raw output](probe-false-qualification-original-source.log)
preserves that negative control. Subcases are not counted as separate methods.

**18 distinct focused methods pass** across the recorded scopes:

| Run | Result and scope |
| --- | --- |
| [Initial](verification-initial.log) | 16 methods: 13 probe cases and three affected RPC error/sanitization cases. |
| [Runtime guard](verification-runtime-guard.log) | Seven affected cases after runtime-before-trace and bounded-input refinements. These repeat prior methods and do not inflate the count. |
| [Final probe](verification-final-probe.log) | 15 probe methods, including two added deadline/call-budget cases. Shared Rpc/error source is unchanged from its three scoped checks. |

The focused tests use fake RPC responses and disposable files. No actual public
provider, archive, marketplace, randomness coordinator, price source or production
service was qualified. No transaction, deployment, key access, existing Anvil,
NFT/LP/balance/journal, website or monitoring state changed. Unchanged full
Solidity/build/size/gas, backend/keeper suites and the deferred capacity campaign
were not rerun.

## Remaining release limits

A passing capability observation stays separate from independent service approval,
full history completeness, provider trust, sustained availability, target-chain
operations and actual PoPL transaction rehearsals. A malicious provider can
fabricate self-consistent replies. Independent price pairs, supported/reviewed
randomness, OpenSea primary-mint integration, actual authority addresses, artwork
publication and an independent audit remain open. Production is **not approved**.
