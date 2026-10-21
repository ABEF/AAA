# Local API wallet coordinator - scoped verification

Reviewed 2026-10-21. Production release remains NOT APPROVED.

## Scope and authorization

The user explicitly retained local Anvil-only signing after automatic approval
review rejected a broader signer extension. That broader proposal was not executed.
The implemented alternative connects the typed API to the existing signer only on
literal-loopback chain31337. Nonlocal configurations remain unsigned; public
DEPLOYMENT stays null. BrowserWallet/BrowserClient and production contracts/backend
are unchanged. No actual wallet extension or chain transaction was used here.

## Changes

- Exact mint, approval, activation/growth and native ETH claim coordination.
- Current contract pins, canonical preparation, account/network/nonce checks and
  shared gas/spending/simulation safeguards before one explicit wallet send.
- Confirmed approval continues to a fresh LP review; a second approval is refused
  in that continuation. Native ETH remains one send; ERC20 at most approval + execution.
- Original journal/hash recovery, cross-tab exclusion and explicit network switching.
- Confirmed-chain/API-lag states distinguished. LP rendering requires the matching
  Entry contribution event and confirmed active NFT position. Pending updates are
  scoped to the affected contribution; no artwork change on approval or claim.

## Executed evidence

- 84 focused cases passed: 57 existing affected API/session cases and 27 new
  coordinator cases, including eleven Python-generated response fixture shapes.
  Tests cover successful actions, exact approvals, wrong network, rejection,
  account changes, stale review, changed code, unknown submission, reload recovery,
  API outage, contribution event/position failure, revert and concurrent attempts.
- Nine isolated headless Chrome scenarios passed: unchanged null-profile simulation,
  mint, native and ZZZ activation, two-step USDC approval/Entry, growth, ETH claim,
  rejection and confirmed/API-lag recovery. Every provider/node is mocked; no real
  extension popup or RPC network funds were accessed.
- Syntax/build checks and exact source bindings are recorded alongside this report.
  All 13 previous shared signer/backend evidence bindings remain byte-identical.
  Unchanged signer/contract suites, full artwork checks and deferred load campaign
  were not rerun. This is scoped internal verification, not an independent audit.

## Initial harness corrections

The first test invocation stopped at a missing test-harness brace. The next run
had two incorrect fixture names and an outage injected into receipt confirmation
instead of the intended API phase. Corrected fixtures yielded 84 passes. The first
browser rejection check lost error code4001 across Playwright's exposed-function
bridge; an explicit error envelope restored actual EIP-1193 rejection semantics.
All nine browser scenarios then passed. Review also corrected expiry-timer carryover
between approval and execution, stale portfolio continuation and pending artwork.

## Remaining boundaries

Actual extension acceptance and an operating API/Anvil rehearsal remain open for
this new coordinator. Existing port8900/Anvil/state were untouched. Replacement
speed-up/cancel discovery is not implemented. Production signer expansion is not
authorized; routes/feeds/RPC/authority/creator terms/VRF/hosting, capacity and
independent audit remain release gates. Publication status is recorded separately.
See [operator steps](../../docs/DEPLOYMENT_WEBSITE.md#local-api-wallet-rehearsal).
