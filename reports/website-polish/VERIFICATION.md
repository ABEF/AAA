# Website gallery, test rewards and confirmed tier feedback

Scope: 2026-10-20 website-only behavior. Contracts, backend accounting and
existing local chains are unchanged; production release remains NOT APPROVED.

- Artwork traits share one row below evolution; fixed rarity multiplier is dim
  while dormant, palette names retain individual colors, pattern name is hidden.
- Single-pool UI omits the selector/filter/column. New preview activation still
  targets ZZZ/WETH; historical demo events are preserved.
- A single saved sample receipt restores claim testing without resetting LP,
  traits or cumulative claims. Its 80% owner pool follows LP, 10% collective is
  equal across active NFTs, separate royalties use active rarity weights.
  Compounding/buyback portions are excluded from holder credits. Duplicate tabs
  and replay cannot fund the same round twice; later activations get no past fee.
- A confirmed upward evolution can play a synchronized supplied audio cue and glow.
  Local mode also requires post-receipt LP growth and unchanged session/account.
  Approvals, claims, failures and same-tier additions do not celebrate. Missing
  image/audio does not change transaction state; reduced motion suppresses glow.

Verification: 77 affected Node cases passed (domain, UI state, reward display,
contribution flow), including five new cases. After tightening unavailable-LP and
image-load feedback guards, the 26 UI-state cases passed again; the other 51
test bodies and domain/contribution/earnings logic were unchanged. Source checks verified all five routes and the
existing 2,784 artwork/metadata pairs. The static build contains 5,588 public files.
No unchanged Solidity/backend suite was rerun for this presentation change.

Browser checks used an isolated static origin on port 4183, preserving the user's
saved 4179 portfolio and local chains. The default three active NFTs showed
$200.74 / $644.34 / $5.48 to claim, with a fourth dormant NFT at zero. Claiming
$5.48 remained zero after reload; lifetime earnings and LP were unchanged.
Activation and a subsequent top-up produced confirmed Activated/Enhanced states
with no past rewards. An Enhanced-to-Singularity contribution showed $10,432 LP,
the `nft-tier-reveal` animation and dialog scrollTop zero only after completion.
No browser errors were observed. Bicolor gallery inspection confirmed one row
and individually colored names; dormant multiplier remained dim.

Compatibility correction: existing local servers allow `artworks.js` but not
`ui-state.js`. Shared effect functions therefore live in the former; no new
server resource permission or chain restart is required. After this relocation,
all 26 UI-state cases passed again. A new read-only browser tab on the existing
8893 deployment loaded all eight confirmed NFTs at block 197, with no console
errors and no pool column. No local transaction was submitted by that check.
This compatibility step was published at `75de6a3` (following `fa4e0b6`);
the later source-bound audio/card follow-up is identified in source-bindings.json.

Operator impact: no contract call, authority, route or service configuration
changed. Demo funding persistence and reset behavior are documented in the
[operator manual](../../docs/OPERATOR_MANUAL.md#main-website-pending-action-and-storage-recovery).
Exact website commit/deployment receipts are recorded separately from this source
record. Public website financial actions remain simulations.

## Supplied ACTI/EV and simplified details follow-up

ACTI replaces the synthesized activation sound. Its entire audible content is
retained (3.69-second exported clip; only surrounding silence removed), as the user
explicitly approved. EV is used for subsequent upward tiers (1.425 seconds).
Audio-only AAC/MP4 assets are compatible with existing local fixture resource
lists. Original MP3 files are unchanged outside the repository. Both assets are
prefetched; decoding is cached after a user gesture. A successful receipt plus
fresh increased LP/higher evolution is required in local mode before scheduling
the reveal. Sound starts in the same render frame as the image crossfade, once
for duplicate card/dialog views; failures cannot reject financial operations.

The final affected UI-state/contribution run passed 33 cases. Its audio case
checks ACTI versus EV selection, same-frame reveal/playback, duplicate suppression
and silent normal refresh/claims. After removing the Previously claimed frame,
three selected local-view cases pass: dormant omission, active earnings/rewards
and fixed rarity weight. Claimed balances and earnings calculations are unchanged.
No unchanged contract/backend suites were rerun. The new build has 5,590 files,
including the two clips. Source/artwork checks retain all 2,784 image/metadata pairs.

Browser QA on the isolated 4183 origin confirmed Dormant -> Activated at $100,
then Enhanced at $1,100, with zero retroactive income, no claimed-total frame and
no console errors. Dialog scroll returns to the updated image. Unit frame evidence
establishes playback scheduling; browser QA is not a physical audio-latency test.
Static previews serve both audio files; the existing local fixture is checked
read-only using GET because it does not implement HEAD. No local test chain restart.

A separate Constellation inlays comparison was created outside both repositories
at the user's request. Existing Orbital rings assets, inventory and metadata are
unchanged. No replacement has been approved.
