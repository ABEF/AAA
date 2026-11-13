# Keeper/RPC audit and focused correction

Baseline `53633b9854b5efea090a91388c3df0c04a5ca3e0`,13November2026.

**Three related probe defects are corrected:** requests continued after access
denial/rate limiting; the logical-only deadline allowed an internal method POST
after its preceding chain check exhausted the budget; and the8-second transport
timeout was not clamped to shorter remaining endpoint time. The probe also now
has an explicit opt-in pacing flag, replacing the need for a one-off wrapper.
These are read-only resource/qualification fixes, not financial authority fixes.

## What changed

`python -m keeper.probe` accepts **`--request-interval-ms 1500`**, or another
reviewed exact integer from0to5000. Omission/default0 retains no pacing and no
new pacing field in the report. A nonzero option is also published as
`request_interval_ms`. It spaces actual HTTP request starts, including the
internal chain identity checks, not just logical calls. Minimum start-to-start
spacing does not add another wait after a response already consumed that time.
No provider is selected or cadence qualified by the new option.

Pacing consumes the same90-second endpoint budget. Existing100logical reads
retain at most two HTTP posts each, now independently capped at200actual posts.
No request starts at/after the endpoint deadline, including between the internal
chain check and method. The original transport timeout is temporarily clamped
to positive remaining time and restored afterward. Access denials401/403/429
and sanitized JSON-RPC rate limits stop further requests to that endpoint;
another explicitly configured endpoint is still assessed independently. The
original denial remains a failed check, not successful missing-block evidence.

The generic Rpc, keeper monitor, nonce/spend/pending journals, source-runtime
profiles, public configurations and signer are unchanged. The probe is not in
`keeper.health.SOURCE_FILES`, so this edit does not change an operating keeper's
stored source identity. No source selection, service/site/Anvil/heartbeat rollout,
signature, public transaction, financial cap or gas default changes.

## Verification

The final **13 unique new methods pass** using the real Rpc chain-check/parser
path over inert wire bytes and a fake monotonic clock. They cover exact default
behavior, each-post pacing, CLI/invalid input and evidence preservation, all
three terminalHTTPstatuses, RPC-rate failure, independent endpoints, unknown-
hash distinctions, between-post and final timeout-capture boundaries, timeout
restoration, unsupported injected pacing and cyclic/deep exception causes.
There are zero network calls, EVM operations, compiler runs or unchanged suite
runs. Earlier11method and final13method stages overlap; do not add their counts.

Initial new regressions fail against the preserved baseline; see
[baseline summary](BASELINE_SUMMARY.json). Its original stdout was a tool result,
not a saved raw log, and the summary labels that provenance. One draft pacing
scenario confused start-to-start spacing with a post-response delay; it was
corrected before final verification, and only that corrected scenario was run
against the immutable baseline. Root review exposed a final clock-capture
boundary; its new regression failed before the last source fix and now passes.
Original outputs and source brackets remain separate. `_remote_error` already
had a four-cause/cycle bound; its new regression preserves that existing control.

## Remaining boundaries

[Task review](TASK_REVIEW.json) records the actually inspected keeper/recovery,
timing/manipulation, diagnostics and dust paths. This is not new execution of
all those existing functions. Pending-first recovery, full125percent signing
padding, current fee-profile recovery, authenticated harvest coalescing and the
strict sampled window retain their existing source-scoped evidence.

The optional pacing must still be qualified against a reviewed provider/tier.
No actual profile was rerun. Sockets/DNS/HTTPheaders may still block until OS or
process supervision intervenes; this is not a hard preemption watchdog. Actual
Linux containment, signer fencing, loss/restore/off-host alerts, full20M/24M
workload and fees, independent markets/providers and operating approval remain
open. A service-only compound policy does not constrain a compromised keeper
key. No broad new policy or custody/economic change was introduced.
