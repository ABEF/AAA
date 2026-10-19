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
- A confirmed upward evolution can play a 1.18-second chime and 1.35-second glow.
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

Operator impact: no contract call, authority, route or service configuration
changed. Demo funding persistence and reset behavior are documented in the
[operator manual](../../docs/OPERATOR_MANUAL.md#main-website-pending-action-and-storage-recovery).
Exact website commit/deployment receipts are recorded separately from this source
record. Public website financial actions remain simulations.
