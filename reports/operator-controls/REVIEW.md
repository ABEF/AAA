# Independent operator controls: internal review - 2026-10-19

Scope: the NFT mint-only switch, Registry disable-only pool path, their confirmed
API fields and operator procedures. Baseline main is
`a99b54b2b84c3e78fc77dcce5528f5739731a8cb`. This is an internal review of the
changes, not an independent audit or production approval.

## Authorization and state transitions

- Both setters use the existing before/after `onlyGovernance` guard. After
  sealing only an approved exact operation executed by the controller can call
  them. No keeper, guardian, token owner, bootstrap or arbitrary caller gains a
  new permission. Governance remains immediate as requested.
- `disablePool` requires an existing identity and at least one disable flag. It
  changes only true-to-false capability flags; repeated stops are idempotent.
  The operation cannot create a pool, change its key/strategy, enable a flag,
  transfer funds or assign a recipient. Its only external guard is the fixed
  controller's authorization check. Token, oracle, hook and wrapper outages do
  not participate in this path.
- Full `configure` / `configureNative` is still necessary to enable flags. It
  retains fresh feed, asset admission and venue/wrapper checks. Reverted
  configuration leaves the stopped state unchanged. An old, still-approved
  enabling operation remains executable if valid: operators must cancel stale
  operations. No control can undo an earlier mined transaction.
- Global pause permits governance configuration. Preparation and locked
  canonical states retain their existing restrictions. Stop flags are not an
  override for handoff locks or a reason to bypass them. The guardian's broader
  global pause remains available; these setters do not confer new guardian powers.

## Mint and callbacks

`mintPaused` is appended to NFT storage and defaults to false. New minting checks
it before the provider request and again after `_safeMint`; a callback which
executes an approved pause cannot leave a committed mint with the flag true.
The entire nested request/payment/ownership operation rolls back. Existing
reentrancy, controller/module, preparation and Vault live guards are unchanged.
No cancellation, second request, reroll, chosen trait or provider replacement is
introduced. Pending original fulfillment and finalization do not read this flag.

Unpausing cannot bypass global pause, locked lifecycle, exhausted supply or a
failed provider. The switch affects new NFT creation only; activation of existing
revealed NFTs, shares, LP fees, royalties, transfers and maintenance retain their
own checks. This is an operational setting, not an economic entitlement exported
by canonical handoff. A successor's desired setting must be configured/reviewed
before its import lock. Import/abort does not automatically reset that setting.

An administrator can still abuse existing immediate governance or withhold
availability. A mint-only pause does not recover permanently unanswered requests
and cannot make whole-collection replacement independent of reveal completion.

## Accounting and dependencies

No Vault, share, reward, royalty, migration, strategy or fee-allocation math was
changed. New flags neither debit nor reassign existing liabilities/principal.
Tests exercise activation/top-up rejection when deposits stop, retained
ownership/claims, successful full-validation reopening, and existing activity
during a mint pause. Mock venues/feeds/VRF are explicit; this is not a target-chain
outage rehearsal. Pool operations stop is not a universal freeze: supported
harvest/receipt/exit paths have independent guards, and broken tokens or venues
can still prevent movement. See the [manual](../../docs/OPERATOR_MANUAL.md).

## API and release boundary

Both protocol and mint-readiness observations read a strict boolean at the same
confirmed block hash and keep the final canonicality/freshness check. The
mint-specific fields do not falsely disable all LP activity and are control
permissions, not execution/provider guarantees. No fallback interprets a missing
or malformed getter as false. Update reviewed deployment code pins and API
compatibility together; an older sealed NFT cannot acquire this getter by
configuration. No browser transaction path was added in this change.

Fresh Slither results are matched to the preceding reviewed expressions; NFT
callback and Registry admission rationales are updated for the new call paths.
The preceding full review is [preserved](previous-slither-review.json).
[Verification](VERIFICATION.md) records actual scopes, failures, source bindings
and limits. No new unauthorized principal-withdrawal path was identified in this
delta; this is not a guarantee that the protocol has no vulnerabilities.

Production authority/provider/runtime selection, real outage and restart
rehearsals, hosted API/wallet operation and independent audit remain open. The
central Todo retains royalty-token outage isolation and broader dependency
availability review; these controls do not solve that separate accounting issue.
