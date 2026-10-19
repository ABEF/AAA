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

### Review-button follow-up - 2026-10-19

The user's token approval was confirmed, but reopening the contribution form
reset its acknowledgement checkbox. Preparation/error messages also appeared
behind the modal. The UI now explains validation failures inside the form,
disables it while preparing, and shows progress/errors beside the review button.
An approved contribution's acknowledgement carries only for its exact session,
wallet, NFT and amount; a changed amount clears it. Approval does not submit Entry.

The artwork Updating badge now belongs only to the NFT whose activation/top-up
confirmed and whose state is being refreshed. Plain refreshes and token approvals
do not mark all artwork as changing. Global stale financial/action guards remain.

**27 focused JavaScript cases pass** (the prior 25 plus amount/acknowledgement
validation and exact contribution-context binding). Browser verification showed
an explicit missing-checkbox message, disabled Preparing transaction controls,
then the actual activation confirmation with its $99 floor for 100 TEST-1 and
separate gas. The confirmation was cancelled; no transaction was submitted by
this review check. Syntax and static packaging were checked. No Solidity/backend
change, service restart, new public-chain test or broad unchanged-suite rerun.
The targeted badge condition was inspected; no additional contribution was sent
solely to retest unchanged accounting. See [the follow-up source hashes](review-feedback-bindings.json).

### Refresh and evolution follow-up - 2026-10-19

The reported activation succeeded on-chain; a read of the original session returned
all four positions available. Its full state read took 20.8 seconds. The UI had
cleared every card during that read, while busy responses could terminate refresh.
Wallet selection also unnecessarily depended on the same complete portfolio.

The follow-up adds fast session wallet inventory, deployment-scoped selection
persistence, single-flight/bounded busy-read retry, dormant financial-row removal,
separate Claim/Grow buttons, and labeled artwork continuity with fresh-data guards.
Artwork crossfades only for a confirmed changed image after loading, respecting
reduced motion. No economic/accounting or production Solidity change occurred.

- **25 affected JavaScript tests pass**, including refresh contention bounds,
  no automatic write retry, confirmed-write/read-failure separation, aborts,
  fast wallet selection, reload/disconnect/session changes, bad inventories and
  dormant/pending presentation. This includes the prior 13 client cases; counts
  are not additive to the initial campaign above.
- **Nine affected HTTP cases pass**, including two new regressions proving that
  session account reads do not wait on the mutation/portfolio lock and an aborted
  browser does not produce a second error response. Retained result on unchanged
  Python bodies; no broad Python or Solidity rerun.
- Syntax/static/artwork checks and the **5,586-file static build pass**. An initial
  check invocation used the wrong `scripts/check.mjs` path; the actual root
  `check.mjs` was then run successfully. No source defect resulted from that typo.
- The [follow-up local campaign](evolution-campaign.json) minted NFT #5 using
  Test wallet B, then executed three exact approvals and activation/top-ups of
  100 / 1,000 / 10,000 TEST-1. All seven typed operations confirmed. Confirmed
  artwork progressed Activated / Enhanced / Singularity, preserving rarity,
  palette and pattern, with zero retroactive LP or royalty claimable balances.
  HTTP timings observed the wallet handshake at 1–55 ms and complete portfolio
  reads at 14.5–24 seconds; these are local observations, not a performance SLA.
- Browser checks verified wallet selection before portfolio completion and after
  reload, dormant rows, distinct active buttons, the growth form, all four cards
  retained during refresh with masked money/disabled actions, and restoration
  after confirmed reads. Crossfade/reduced-motion logic was reviewed; no
  frame-by-frame animation recording or production load test is claimed.

[Follow-up bindings](refresh-bindings.json) identify the final affected sources.
All 40 production Solidity source bindings match the original artifact evidence.
The disposable service was restarted to apply the session endpoint; old receipts
and a raw chain dump were retained externally, not promoted to qualified recovery.
Test wallet A's original four seeded NFTs were not altered by the follow-up
transaction campaign. A/B transfers are ownership tests, not marketplace sales.
Public services, the website deployment and paused monitoring are unchanged.

Independent-device/shared-pool concurrency, stale quotes/ownership races, browser
signing/nonces, provider failures and production load remain central Todo gates.
The two-account local service retains its serial lock and must stay loopback-only.

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
