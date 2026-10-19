# Local website integration: scoped verification

2026-10-19. **Internal local evidence; production release NOT APPROVED.**

The existing website now runs against the disposable deployment through an
explicit loopback `/app/` mount. The public server remains unchanged. There are
no public transactions, production key reads, Solidity changes or monitor restart.

## Executed checks

### Presentation follow-up, 2026-10-19

The local card now shows the fixed revealed rarity multiplier, gray while dormant,
and dormant details omit the claim action. JavaScript syntax and diff checks pass.
Browser inspection at local block 109 verified the dormant Rare card's ×2 in
RGB(139,147,161), active Commun ×1 / Rare ×2 in RGB(59,215,235), no dormant claim
button with activation/transfer retained, and an active claim button still disabled
when there are no funds. Unrevealed labels are explicitly unknown. No transaction
was submitted for these checks; no accounting, API or contract code changed.
Unchanged test suites were not rerun. The source-binding file below describes
the original integration snapshot, not these later website presentation changes.
Todo, feature reference, local guide, operator notes and project context are aligned.
No operator call/restart or public deployment is required for this local UI fix.

### Original integration campaign

- **33 integration assertions passed** using the new confirmation API and actual
  local receipts: exact approval separate from Entry; approval leaves the NFT
  dormant; $100 activation and top-up add at least $99 LP; no retroactive fees;
  fixed traits; ownership transfer invalidates old drafts; the buyer inherits
  both fee streams; bounded wallet claims; actual mint/reveal; cumulative royalty
  claims; missing ETH USD remains null; identical operation IDs return the saved
  outcome without resubmission. [Recorded campaign](integration.json).
- **47 distinct focused Python cases pass across scoped runs:** 35 existing
  launcher/HTTP/recovery checks on the modified service, plus 12 new confirmation
  and static-boundary cases. The initial combined run had 44 passes; the final
  12-case run includes those nine new cases and three supplemental cases for
  bounded wallet claims, increased gas rejection and static-file traversal.
  Repeated cases are not counted twice.
- **60 JavaScript cases pass:** 47 existing domain/artwork cases plus 13 new
  client cases covering exact loopback gating, uint256 values, unavailable prices,
  currencies, wrong chain, read failures, account changes, expiry, storage failure,
  lost-response replay, session restart and uncertain/failed receipts. The final
  client-only run followed formatting/schema refinements; unchanged domain cases
  were not rerun. JS syntax, the existing static/artwork check, and the final
  5,586-file static build pass.
- Browser inspection on the existing design confirmed the four actual NFTs,
  disclosed local/mock boundaries, revealed artwork, confirmed LP and both fee
  streams. A 99-token input was blocked; 100 required exact approval followed by
  a separate Entry confirmation with a $99 floor and separate gas. The resulting
  NFT showed $100 attached LP, Activated artwork and zero historical fees.
  On the clean final session, Escape cancelled a prepared 0.05 test-ETH mint
  without changing the four-NFT supply. Claiming NFT #2 paid its TEST-1 LP fees
  and ETH royalties together, cleared both claimable balances, increased the
  lifetime per-currency total and preserved LP value and earned history.

The integration campaign used a separate disposable session. A clean final
deployment is left running for the user; earlier receipts remain external.
The generic panel on the user's original port is not replaced.

## Corrections and review

Browser testing caught an unbound native `fetch` invocation; the adapter now
calls it through a wrapper. A Windows text-edit helper temporarily changed UTF-8
symbols; the original app was reconstructed from Git and all task edits reapplied
with explicit UTF-8/LF. Final syntax/diff/browser checks cover the corrected files.

Internal review tightened the static mount: allowlisted top-level files only,
explicit public asset extensions, no `..` segments, resolved containment in the
website and assets directory. The final static-boundary regression covers this
post-campaign change; transaction code was unchanged. Inline styles are allowed
for the established artwork, while scripts/connect sources stay same-origin.

Confirmation intent is typed, stored server-side, account/revision-bound and
expires on both monotonic and chain clocks. Approval and Entry are never silently
combined. Exact calldata is freshly simulated; increased accepted gas/price
requirements reject submission. The existing durable operation ledger handles
duplicate requests and uncertain writes. Browser storage must succeed before
submission. Failed API reads clear projections, preserving unavailable values.
Full IDs remain strings; ordinal labels do not change custody identity.

## Reuse and limits

[Source bindings](source-bindings.json) record the current local implementation,
website files and 40 unchanged production Solidity sources. The launcher verified
every reused artifact's source metadata. No unchanged Solidity suites or full
production build were rerun. The new local test does not replace the historical
broader keeper/canonical/earnings evidence.

The actual core uses a **mock venue, mock $1 feeds and mock randomness**. Entry
uses an already-pair test token, not the unqualified public conversion routes.
Local account submission is not production EIP1193 signing. One local confirmation
is not production finality; mempool replacement/reorgs, provider accounts/networks,
production route/price qualification, remote/canonical portfolio states, large
history/load and independent review remain open. The optional royalty reporting
profile/converter is not enabled in this fixture, so no new outage/conversion UI
qualification is claimed. The local service must never be Internet-exposed.

Procedures: [local website](../../docs/LOCAL_WEBSITE.md),
[operator manual](../../docs/OPERATOR_MANUAL.md#disposable-local-testing).
Status: [central Todo](../../TODO.md), not a second checklist here.
